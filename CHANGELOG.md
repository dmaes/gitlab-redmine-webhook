# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-01-06

### Changed
* Bump python to 3.14.3
* Bump gunicorn from 23.0.0 to 25.0.1
* Bump certifi from 2025.11.12 to 2026.1.4
* Bump packaging from 25.0 to 26.0
* Bump urllib3 from 2.5.0 to 2.6.3
* Bump werkzeug from 3.1.3 to 3.1.5

### Fixed
* Fix regex matching for multiple issue references

## [0.2.0] - 2025-12-23

### Changed
* Append commits to last note, if that note is a commits note for the same project.
* Allow choosing between private and public notes with `X-GitlabRedmine-Private-Notes: true`

### Added
* Support for Release events

## [0.1.1] - 2025-12-17

### Changed
* container: also listen on IPv6

### Fixed
* Detect existing commit notes, and don't duplicate them


## [0.1.0] - 2025-11-20

Initial Release
