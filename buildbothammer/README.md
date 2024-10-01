# BuildbotHammer

This app automatically creates revert Pull Requests for failing builds in the
CPython project. It monitors Buildbot for failing builds, identifies the
commit that caused the failure, and creates a revert PR on GitHub. It also sends
notifications to Discord.

## Prerequisites

- Python 3.11+
- Git
- A GitHub account with fork of the CPython repository
- A Discord server with webhook set up (for notifications)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/python/buildmasterconf.git
   cd buildmasterconf/buildbot-hammer
   ```

2. Install the required Python packages:
   ```
   pip install -e .
   ```

3. Set up environment variables:
   ```
   export GITHUB_TOKEN="your-github-personal-access-token"
   export DISCORD_WEBHOOK_URL="your-discord-webhook-url"
   ```

4. Update the script with your GitHub username:
   Open the script and replace `FORK_OWNER` variable with your GitHub username.

5. (Optional) Update the `REPO_CLONE_DIR` path if you want to use a different location for the local CPython clone.

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
- `REPO_CLONE_DIR`: The directory for the local clone of the repository