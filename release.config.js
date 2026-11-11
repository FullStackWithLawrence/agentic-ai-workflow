// semantic-release, run by .github/workflows/release.yml.
//
// It reads the conventional commits since the last tag (fix: a patch release,
// feat: a minor release, BREAKING CHANGE: a major release), writes the version
// into app/__version__.py, pyproject.toml and the Dockerfile's image label
// (scripts/bump_version.py), updates CHANGELOG.md, commits them, tags the
// commit v<version>, and publishes a GitHub release. alpha and beta make
// prereleases, e.g. 0.2.0-alpha.1.
module.exports = {
  branches: [
    "main",
    { name: "beta", prerelease: true },
    { name: "alpha", prerelease: true },
  ],
  plugins: [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      {
        changelogFile: "CHANGELOG.md",
        changelogTitle: `# Change Log\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).\n\n`,
      },
    ],
    [
      "@semantic-release/exec",
      {
        prepareCmd: "python scripts/bump_version.py ${nextRelease.version}",
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: ["CHANGELOG.md", "app/__version__.py", "pyproject.toml", "Dockerfile"],
        message: "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}",
      },
    ],
    "@semantic-release/github",
  ],
};
