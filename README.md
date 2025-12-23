# Gitlab Redmine Webhook

Webhook for Gitlab to link commits and MR's to referenced issues in Redmine

## Configuration

| Env var | Required | Description | Default value |
|---|---|---|---|
| `REDMINE_URL` | required | URL of the Redmine instance | |
| `REDMINE_KEY` | required | Redmine API Key | |
| `REDMINE_USER_ID` | required | ID of the user to whom the API key belongs | |
| `LOG_LEVEL` | optional | Log level | `INFO` |
| `LOG_FORMAT` | optional | Set to `json` for json formatted logs | `` |

## Endpoints

### `/health`

Returns `"OK"`

### `/hook`

#### Supported values for `X-Gitlab-Event`:

* `Merge Request Hook`
* `Push Hook`
* `Release Hook`

#### Additional supported headers

* `X-GitlabRedmine-Private-Notes`: Set to `true` to create private notes instead of public ones (not case sensitive).
