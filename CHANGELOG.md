# Changelog

## 0.2.0 - 2026-11-15

**Change notice: `username` is being renamed to `handle`.**
The API now sends a user's login name as `handle`; older responses still send `username`.
`opsclient` accepts either name, so no action is needed and existing code keeps working.
In Python the value is still read as `user.username`; that will not change in 0.x releases.
If the API sends both fields, `username` wins. Support for the old name stays until the API drops it.

Also in this release:
- GET requests retry up to 3 times with exponential backoff on timeouts, network errors and 5xx.
  POST requests are never retried, to avoid creating duplicates.
- New `OpsServerError` for 5xx responses (a subclass of `OpsApiError`).
- Settings from `OPS_*` environment variables; JSON logs on stderr.

## 0.1.0 - 2026-11-14

- First version: `OpsClient` with `get`, `list`, `create`; `User`, `Post`, `NewPost` models;
  `ops list-users` command.
