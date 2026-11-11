// Conventional commits, which semantic-release reads to version the app.
module.exports = {
  extends: ["@commitlint/config-conventional", "@commitlint/config-angular"],
  rules: {
    // commit messages have one paragraph, or bullet list, per line (one git commit -m per
    // paragraph), so their body and footer lines are longer than config-conventional's 100.
    "body-max-line-length": [0, "always"],
    "footer-max-line-length": [0, "always"],
    // config-angular's types, plus chore, for housekeeping and releases.
    "type-enum": [
      2,
      "always",
      ["build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test"],
    ],
  },
};
