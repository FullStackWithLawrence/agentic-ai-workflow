# 12-Factor Methodology

This project conforms to [12-factor methodology](https://12factor.net/). The 12-Factor methodology is a set of best practices for building modern, scalable, maintainable software-as-a-service apps. These principles were first presented by engineers at Heroku, a cloud platform as a service (PaaS) company. Following are the salient points of how this project adopts these best practices.

- 1. **Codebase**: [✅] One codebase tracked in revision control, many deploys
- 2. **Dependencies**: [✅] Explicitly declare and isolate dependencies. We're using a Python virtual environment along with a requirements.txt file to manage package versions. We also use Dependabot and Mergify on GitHub Actions to periodically monitor and update package versions.
- 3. **Config**: [✅] Store config in the environment. This project implements a special [.env](../.env) file, which locally stores all configuration information for the package.
- 4. **Backing services**: [✅] Treat backing services as attached resources. We're using remote [OpenAI Api](https://openai.com/) and [MySql](https://www.mysql.com/)
- 5. **Build, release, run**: [✅] Strictly separate build and run stages. 1-click `init`, `build`, `test`, `run`, `release` and `tear-down` are implemented in Makefile.
- 6. **Processes**: [✅] Execute the app as one or more stateless processes. Our app runs from the command line, but it could be repurposed as a backing service for a REST Api.
- 7. **Port binding**: [✅] Export services via port binding. This **could** be implemented as micro service listening on ports 80 and 443.
- 8. **Concurrency**: [✅] Scale out via the process model. We implement a single, stateless agentic workflow in this app.
- 9. **Disposability**: [✅] Maximize robustness with fast startup and graceful shutdown. Makefile implemenent `tear-down` as a 1-click way to dispose of the environment.
- 10. **Dev/prod parity**: [✅] Keep development, staging, and production as similar as possible. The repo for this project has `alpha`, `beta`, `next`, and `main` branches.
- 11. **Logs**: [✅] Treat logs as event streams. We get this "for free" from Python logging.
- 12. **Admin processes**: [✅] Run admin/management tasks as one-off processes. All admin processes are implemented with GitHub Actions and other GitHub management features.

Additionally, we leverage pre-commit to enforce code formatting, linting and to check all of the follow on each commit:

```console
codespell................................................................Passed
prettier.................................................................Passed
black................................................(no files to check)Skipped
flake8...............................................(no files to check)Skipped
isort................................................(no files to check)Skipped
pylint...............................................(no files to check)Skipped
bandit...............................................(no files to check)Skipped
fix utf-8 byte order marker..............................................Passed
fix python encoding pragma (deprecated)..............(no files to check)Skipped
check for case conflicts.................................................Passed
check json...........................................(no files to check)Skipped
check for merge conflicts................................................Passed
check for broken symlinks............................(no files to check)Skipped
check toml...............................................................Passed
check xml............................................(no files to check)Skipped
check yaml...........................................(no files to check)Skipped
detect destroyed symlinks................................................Passed
detect aws credentials...................................................Passed
detect private key.......................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
check for case conflicts.................................................Passed
check for merge conflicts................................................Passed
debug statements (python)............................(no files to check)Skipped
```
