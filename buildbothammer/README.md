# BuildbotHammer

This app automatically creates revert Pull Requests for failing builds in the
CPython project. It monitors Buildbot for failing builds, identifies the
commit that caused the failure, and creates a revert PR on GitHub. It also sends
notifications to Discord.

## Usage

Run the script with:

```
python -m buildbothammer
```

The script will:
1. Check Buildbot for failing builds
2. For each failing build, it will:
   - Identify the commit that caused the failure
   - Create a new branch in your fork
   - Revert the problematic commit
   - Create a Pull Request to the main CPython repository
   - Send a notification to the configured Discord channel

## Configuration

- `BUILDBOT_API`: The Buildbot API endpoint (default: "http://buildbot.python.org/api/v2")
- `BUILDBOT_URL`: The Buildbot URL for generating links (default: "http://buildbot.python.org/#/")
- `REPO_OWNER`: The owner of the main repository (default: "python")
- `REPO_NAME`: The name of the repository (default: "cpython")
- `FORK_OWNER`: Your GitHub username (default: "$REPO_OWNER")
- `REPO_CLONE_PATH`: The directory for the local clone of the repository