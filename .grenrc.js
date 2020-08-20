/* .grenrc.js */
module.exports = 
{
    "dataSource": "commits",
    "includeMessages": "merge",
    "ignore-commits-with": [
        "pythonapp.yml",
        "set theme",
        "Update issue templates",
        "version update"
    ],
    "ignoreIssuesWith": [
        "wontfix",
        "duplicate"
    ],
    "template": {
        "commit": ({ message, url, author, name }) => `- [${message}](${url}) - ${author ? `@${author}` : name}`,
        "issue": "- {{labels}} {{name}} [{{text}}]({{url}})",
        "label": "[**{{label}}**]",
        "noLabel": "closed",
        "group": "\n#### {{heading}}\n",
        "changelogTitle": "# Changelog\n\n",
        "release": "## {{release}} ({{date}})\n{{body}}",
        "releaseSeparator": "\n---\n\n"
    },
    "groupBy": {
        "Enhancements:": ["enhancement", "internal","feature"],
        "Bug Fixes:": ["bug","fix"],
        "Other": ["*"]
    }
}