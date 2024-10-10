import aiohttp
import asyncio
import json
import os
import logging
from pathlib import Path
import subprocess
from filelock import FileLock
from github import Github
from github.GithubException import GithubException

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BUILDBOT_API = "http://buildbot.python.org/api/v2"
BUILDBOT_URL = "http://buildbot.python.org/#/"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    logger.warning(
        "DISCORD_WEBHOOK_URL environment variable is not set. Discord notifications will be disabled."
    )

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN environment variable is not set")

N_BUILDS = 200

REPO_OWNER = "python"
REPO_NAME = "cpython"
FORK_OWNER = os.getenv("FORK_OWNER", REPO_OWNER)
REPO_CLONE_PATH = os.getenv("REPO_CLONE_PATH")
if not REPO_CLONE_PATH:
    raise EnvironmentError("REPO_CLONE_PATH environment variable is not set")
REPO_CLONE_DIR = Path(REPO_CLONE_PATH)
LOCK_FILE = REPO_CLONE_DIR.parent / f"{REPO_NAME}.lock"
MIN_CONSECUTIVE_FAILURES = 3


class BuildbotError(Exception):
    """Exception raised for errors in the Buildbot API."""

    pass


class GitHubError(Exception):
    """Exception raised for errors in GitHub operations."""

    pass


def generate_build_status_graph(builds):
    status_map = {
        0: "🟩",  # Success
        2: "🟥",  # Failure
        None: "⬜",  # Not completed
        1: "🟧",  # Warnings or unstable
    }
    return "".join(status_map.get(build["results"], "⬜") for build in builds)


async def send_discord_notification(session, message):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord notification not sent: DISCORD_WEBHOOK_URL is not set")
        return

    payload = {"content": message}

    try:
        async with session.post(DISCORD_WEBHOOK_URL, json=payload) as response:
            if response.status == 204:
                logger.info("Successfully sent Discord notification")
            else:
                logger.error(
                    f"Failed to send Discord notification. Status: {response.status}"
                )
    except Exception as e:
        logger.error(f"Error sending Discord notification: {str(e)}")


async def fetch(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return await response.json()
            elif "text/plain" in content_type:
                text = await response.text()
                return json.loads(text)
            else:
                raise ValueError(f"Unexpected content type: {content_type}")
    except aiohttp.ClientResponseError as e:
        raise BuildbotError(f"HTTP error {e.status} while fetching {url}: {e.message}")
    except json.JSONDecodeError:
        raise BuildbotError(f"Failed to decode JSON from {url}")


async def get_builder_builds(session, builder, limit=N_BUILDS):
    builds_url = f"{BUILDBOT_API}/builders/{builder['builderid']}/builds?limit={limit}&&order=-complete_at"
    builds = await fetch(session, builds_url)
    status_graph = generate_build_status_graph(builds["builds"])
    return builder, builds["builds"], status_graph


def is_failing_builder(builds):
    failing_streak = 0
    first_failing_build = None
    for build in builds:
        if not build["complete"]:
            continue
        if build["results"] == 2:  # 2 indicates a failed build in Buildbot
            failing_streak += 1
            first_failing_build = build
            continue
        elif build["results"] == 0:  # 0 indicates a successful build in Buildbot
            if failing_streak >= MIN_CONSECUTIVE_FAILURES:
                return True, first_failing_build
            return False, None
        failing_streak = 0
    return False, None


async def get_failing_builders(session, limit=N_BUILDS):
    logger.info("Fetching failing builders")
    builders_url = f"{BUILDBOT_API}/builders"
    builders = await fetch(session, builders_url)
    builders = builders["builders"]

    relevant_builders = [
        b for b in builders if "3.x" in b["tags"] and "stable" in b["tags"]
    ]

    failing_builders = []
    all_builders_status = []

    async def process_builder(builder):
        try:
            builder, builds, status_graph = await get_builder_builds(session, builder, limit)
            is_failing, last_failing_build = is_failing_builder(builds)
            if last_failing_build:
                status_graph = list(status_graph)
                status_graph[builds.index(last_failing_build)] = "🟪"
                status_graph = "".join(status_graph)
                print(f"{builder['name']}\n{status_graph}\n")
            all_builders_status.append((builder["name"], status_graph))
            if is_failing:
                logger.info(
                    f"Found failing builder: {builder['name']} with last failing build {last_failing_build['buildid']}"
                )
                failing_builders.append((builder, last_failing_build))
            else:
                logger.debug(f"Builder {builder['name']} is not failing")
        except Exception as e:
            logger.error(f"Error processing builder {builder['name']}: {str(e)}")

    async with asyncio.TaskGroup() as tg:
        for builder in relevant_builders:
            tg.create_task(process_builder(builder))

    logger.info(f"Total failing builders found: {len(failing_builders)}")
    return failing_builders, all_builders_status


async def get_change_request(session, build):
    logger.info(f"Fetching change request for build: {build['buildid']}")
    changes_url = f"{BUILDBOT_API}/builds/{build['buildid']}/changes"
    changes = await fetch(session, changes_url)

    if len(changes["changes"]) == 1:
        logger.debug(f"Found change request for build {build['buildid']}")
        return changes["changes"][0]
    else:
        logger.debug(f"No single change request found for build {build['buildid']}")
        return None


def run_command(command, cwd=None, check=True, capture_output=False):
    logger.debug(f"Running command: {' '.join(command)}")
    subprocess.run(
        command, cwd=cwd, capture_output=capture_output, text=True, check=check
    )


def ensure_repo_clone():
    if not REPO_CLONE_DIR.exists():
        logger.info(f"Cloning repository to {REPO_CLONE_DIR}")
        clone_url = f"https://{GITHUB_TOKEN}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
        run_command(["git", "clone", clone_url, str(REPO_CLONE_DIR)])
    else:
        logger.info("Updating existing repository clone")
        run_command(["git", "fetch", "--all"], cwd=str(REPO_CLONE_DIR))
        run_command(["git", "reset", "--hard", "origin/main"], cwd=str(REPO_CLONE_DIR))


def check_existing_pr(repo, branch_name):
    logger.info(f"Checking for existing PR for branch: {branch_name}")
    existing_prs = repo.get_pulls(state='open', head=f"{FORK_OWNER}:{branch_name}")
    return next(existing_prs, None)


def create_revert_pr(commit_sha, builder, failing_build):
    logger.info(f"Creating revert PR for commit: {commit_sha}")
    g = Github(GITHUB_TOKEN)

    try:
        main_repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")

        branch_name = f"revert-{commit_sha[:7]}"
        
        # Check for existing PR
        existing_pr = check_existing_pr(main_repo, branch_name)
        if existing_pr:
            logger.info(f"Existing PR found: {existing_pr.html_url}")
            return None, None

        with FileLock(LOCK_FILE):
            ensure_repo_clone()


        with FileLock(LOCK_FILE):
            ensure_repo_clone()

            run_command(
                ["git", "config", "user.name", "Your Name"], cwd=str(REPO_CLONE_DIR)
            )
            run_command(
                ["git", "config", "user.email", "your.email@example.com"],
                cwd=str(REPO_CLONE_DIR),
            )

            run_command(["git", "checkout", "-b", branch_name], cwd=str(REPO_CLONE_DIR))
            logger.info(f"Created and checked out new branch: {branch_name}")

            run_command(
                ["git", "revert", "--no-edit", commit_sha], cwd=str(REPO_CLONE_DIR)
            )
            logger.info(f"Successfully reverted commit {commit_sha}")

            run_command(
                [
                    "git",
                    "push",
                    "-f",
                    f"https://{GITHUB_TOKEN}@github.com/{FORK_OWNER}/{REPO_NAME}.git",
                    branch_name,
                ],
                cwd=str(REPO_CLONE_DIR),
            )
            logger.info("Pushed changes to fork")

            commit_to_revert = main_repo.get_commit(commit_sha)
            original_commit_message = commit_to_revert.commit.message.split("\n")[0]

            commit_to_revert = main_repo.get_commit(commit_sha)
            original_commit_message = commit_to_revert.commit.message.split("\n")[0]
            author = (
                commit_to_revert.author.login if commit_to_revert.author else "Unknown"
            )
            commit_date = commit_to_revert.commit.author.date.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

            pr_description = f"""
🔄 **Automatic Revert**

This PR automatically reverts commit {commit_sha} due to a failing build.

📊 **Build Information:**
- Builder: {builder['name']}
- Build Number: {failing_build['number']}
- Build URL: {BUILDBOT_URL}/builders/{failing_build['builderid']}/builds/{failing_build['buildid']}

💻 **Reverted Commit Details:**
- SHA: `{commit_sha}`
- Author: {author}
- Date: {commit_date}
- Message: "{original_commit_message}"

🛠 **Next Steps:**
1. Investigate the cause of the build failure.
2. If the revert is necessary, merge this PR.
3. If the revert is not necessary, close this PR and fix the original issue.

⚠️ Please review this revert carefully before merging.

cc @{author} - Your attention may be needed on this revert.
"""
            pr = main_repo.create_pull(
                title=f"🔄 Revert: {original_commit_message}",
                body=pr_description,
                head=f"{FORK_OWNER}:{branch_name}",
                base="main",
            )

            logger.info(f"Created revert PR: {pr.html_url}")

            discord_message = f"""
🚨 **Automatic Revert PR Created**

A build failure has triggered an automatic revert. Details:

🔗 **PR Link:** {pr.html_url}
🏗 **Failed Build:** {BUILDBOT_URL}/builders/{failing_build['builderid']}/builds/{failing_build['buildid']}
🔄 **Reverted Commit:** `{commit_sha}`
✍️ **Original Author:** {author}
📅 **Commit Date:** {commit_date}
💬 **Commit Message:** "{original_commit_message}"

Please review and take appropriate action!
"""

            return pr.html_url, discord_message
    except GithubException as e:
        raise GitHubError(f"GitHub API error: {e.status}, {e.data}")
    except Exception as e:
        raise GitHubError(f"Unexpected error while creating revert PR: {str(e)}")
    finally:
        run_command(
            ["git", "revert", "--abort"],
            cwd=str(REPO_CLONE_DIR),
            check=False,
            capture_output=True,
        )
        run_command(["git", "checkout", "main"], cwd=str(REPO_CLONE_DIR))
        run_command(["git", "branch", "-D", branch_name], cwd=str(REPO_CLONE_DIR))


async def process_builder(session, builder, first_failing_build):
    try:
        change_request = await get_change_request(session, first_failing_build)

        if change_request and "sourcestamp" in change_request:
            commit_sha = change_request["sourcestamp"]["revision"]
            pr_url, discord_message = create_revert_pr(
                commit_sha, builder, first_failing_build
            )
            if pr_url and discord_message:
                logger.info(f"Created revert PR for commit {commit_sha}: {pr_url}")
                await send_discord_notification(session, discord_message)
            else:
                logger.error(f"Failed to create revert PR for commit {commit_sha}")
        else:
            logger.warning(
                f"No suitable change request found for builder: {builder['name']}"
            )
    except (BuildbotError, GitHubError) as e:
        logger.error(f"Error processing builder {builder['name']}: {str(e)}")
        raise


async def main():
    logger.info("Starting the Async Buildbot and GitHub Revert Script")

    async with aiohttp.ClientSession() as session:
        try:
            failing_builders, all_builders_status = await get_failing_builders(session)

            results = await asyncio.gather(
                *[
                    process_builder(session, builder, first_failing_build)
                    for builder, first_failing_build in failing_builders
                ],
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in processing a builder: {result}")
        except Exception as e:
            logger.error(f"An error occurred in the main execution: {str(e)}")
        finally:
            logger.info("Buildbothammer execution completed")


if __name__ == "__main__":
    asyncio.run(main())
