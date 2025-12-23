import flask
from flask import Flask, request
from flask_restful import Resource, Api

import json

import logging
import logging.config
from pythonjsonlogger.json import JsonFormatter

import os
import re
import sys
import uuid

from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError

ISSUE_RE = '(^| |\\n|\\(|\\[)#([0-9]+)(\\]|\\)| |\\n|$)'

redmine_url = os.environ.get('REDMINE_URL')
redmine_key = os.environ.get('REDMINE_KEY')
my_user_id = int(os.environ.get('REDMINE_USER_ID'))

if not (redmine_url and redmine_key and my_user_id):
    print("Must specify REDMINE_URL, REDMINE_KEY and REDMINE_USER_ID")
    sys.exit(1)

app = Flask(__name__)
api = Api(app)

redmine = Redmine(
        redmine_url,
        key=redmine_key,
        )

access_log = logging.getLogger('werkzeug')
access_log.propagate = False


def get_request_id():
    if getattr(flask.g, 'request_id', None):
        return flask.g.request_id

    new_uuid = uuid.uuid4().hex[:10]
    flask.g.request_id = new_uuid

    return new_uuid


class RequestIdFilter(logging.Filter):
    # This is a logging filter that makes the request ID available for use in
    # the logging format. Note that we're checking if we're in a request
    # context, as we may want to log things before Flask is fully loaded.
    def filter(self, record):
        record.request_id = get_request_id() if flask.has_request_context() else ''
        return True


log = logging.getLogger()
log.handlers = []
app_log_handler = logging.StreamHandler(sys.stdout)
app_log_handler.addFilter(RequestIdFilter())
if os.environ.get('LOG_FORMAT') == 'json':
    app_log_handler.setFormatter(JsonFormatter(
        ['asctime', 'request_id', 'levelname', 'message'],
        rename_fields={'asctime': 'time', 'levelname': 'level'}))
else:
    app_log_handler.setFormatter(
            logging.Formatter('[%(asctime)s] ID:%(request_id)s - %(levelname)s: %(message)s')
            )
log.addHandler(app_log_handler)
log.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def get_event_project_md_link(event):
    path = event['project']['path_with_namespace']
    web_link = event['project']['web_url']
    return f"[{path}]({web_link})"


def find_mr_issues(event):
    mr = event['object_attributes']
    issues = []

    for m in re.findall(ISSUE_RE, mr['title']):
        issues.append(m[1])

    for m in re.findall(ISSUE_RE, mr['description']):
        issues.append(m[1])

    return set(issues)


def find_commits_issues(event):
    issueCommits = dict()

    for commit in event['commits']:
        matches = re.findall(ISSUE_RE, commit['message'])
        issues = []
        for match in matches:
            issues.append(match[1])
        for issue in set(issues):
            if issue not in issueCommits:
                issueCommits[issue] = []
            issueCommits[issue].append(commit)

    return issueCommits


def get_mr_link(event):
    mr = event['object_attributes']
    project_path = event['project']['path_with_namespace']
    return f"[{project_path}!{mr['iid']}]({mr['url']})"


def issue_has_mr_note(issue, event):
    escaped_link = re.escape(get_mr_link(event))
    notes_re = re.compile(f"^Merge Request {escaped_link} referencing this issue .+$")

    for journal in issue.journals:
        if journal.user.id == my_user_id and notes_re.match(journal.notes):
            return True

    return False


def issue_has_commit_note(issue, event, sha):
    project_escaped_link = re.escape(get_event_project_md_link(event))
    header_re = re.compile(f"^[0-9]+ new commits pushed to {project_escaped_link} referencing this issue:")
    commit_re = re.compile(f".+ \\* \\[{sha}\\].+")
    project_url = event['project']['web_url']

    for journal in issue.journals:
        if journal.user.id == my_user_id and header_re.match(journal.notes):
            log.debug(f"Found existing note on #{issue.id} for {project_url}")
            if commit_re.match(journal.notes.replace("\n", ' ')):
                log.debug(f"Found existing note on #{issue.id} for {sha} in {project_url}")
                return True

    log.debug(f"Found no existing note on #{issue.id} for {sha} in {project_url}")
    return False


def should_append_commits_to_last_note(issue, event):
    project_escaped_link = re.escape(get_event_project_md_link(event))
    header_re = re.compile(f"^[0-9]+ new commits pushed to {project_escaped_link} referencing this issue:")

    try:
        *_, last_journal = issue.journals
        if last_journal.user.id == my_user_id and header_re.match(last_journal.notes):
            return last_journal
    except ValueError:
        pass

    return None


def update_redmine_issue_mr(id, event):
    mr = event['object_attributes']

    # No need to notify whenever new commits are pushed
    if 'oldrev' in mr:
        return "skipped"

    try:
        issue = redmine.issue.get(id)
    except ResourceNotFoundError:
        return "not found"

    mr_action = mr['action']
    action = f"{mr_action}d" if mr_action[-1] == 'e' else f"{mr_action}ed"

    # Not need to notify on every update
    if mr_action == 'update' and issue_has_mr_note(issue, event):
        return "skipped"

    issue.notes = f"Merge Request {get_mr_link(event)} referencing this issue has been {action}."

    issue.private_notes = True
    issue.save()

    return "updated"


def update_redmine_issue_commits(id, event, commits):
    try:
        issue = redmine.issue.get(id)
    except ResourceNotFoundError:
        return "not found"

    c_len = len(commits)
    link = get_event_project_md_link(event)
    header = f"{c_len} new commits pushed to {link} referencing this issue:"

    commit_notes = []

    for commit in commits:
        sha = commit['id'][0:8]
        author = commit['author']['name']
        title = commit['title']
        url = commit['url']
        if not issue_has_commit_note(issue, event, sha):
            commit_notes.append(f"* [{sha}]({url}) {author}: {title}")

    if len(commit_notes) == 0:
        return "skipped"

    append_to = should_append_commits_to_last_note(issue, event)
    if append_to:
        log.debug(f"Appending commits to note {append_to} on #{issue.id}")
        commit_notes = append_to.notes.split("\n")[1:] + commit_notes
        commit_note = "\n".join(commit_notes)
        header = f"{len(commit_notes)} new commits pushed to {link} referencing this issue:"
        append_to.notes = f"{header}\n{commit_note}"
        append_to.save()
    else:
        log.debug(f"Creating new note with commits on #{issue.id}")
        commit_note = "\n".join(commit_notes)
        header = f"{len(commit_notes)} new commits pushed to {link} referencing this issue:"

        issue.notes = f"{header}\n{commit_note}"
        issue.private_notes = True
        issue.save()

    return "updated"


class Health(Resource):
    def get(self):
        return 'OK'


class Hook(Resource):
    def log_request(self):
        event = request.headers.get("X-Gitlab-Event")
        glab_instance = request.headers.get("X-Gitlab-Instance")
        event_uuid = request.headers.get("X-Gitlab-Event-Uuid")
        log.info(f"Received '{event}' event '{event_uuid}' from {glab_instance}")
        headers_dict = {k: v for k, v in request.headers.to_wsgi_list()}
        log.debug(f"Headers: {headers_dict}")
        log.debug(f"Body: {json.dumps(request.get_json())}")

    def post(self):
        event = request.headers.get("X-Gitlab-Event")
        self.log_request()

        if event == 'Push Hook':
            return self.handle_push()
        elif event == 'Merge Request Hook':
            return self.handle_mr()
        else:
            log.error(f"Unknown event type '{event}'")
            return {'error': f"Unknown event '{event}'"}, 400

    def handle_mr(self):
        event = request.get_json()
        res = dict()
        for issue in find_mr_issues(event):
            res[issue] = update_redmine_issue_mr(issue, event)
        return {'issues': res}

    def handle_push(self):
        event = request.get_json()
        issue_commits = find_commits_issues(event)
        res = dict()
        for issue, commits in issue_commits.items():
            res[issue] = update_redmine_issue_commits(issue, event, commits)
        return {'issues': res}


api.add_resource(Health, '/health')
api.add_resource(Hook, '/hook')
