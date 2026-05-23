"""CLI 命令行界面模块"""

import click

# ── Banner ──

BANNER = (
    "   _____    ____     ____        __          _____                    __                   \n"
    "  / ___/   / __ \   / __ \      / /         / ___/   __  __   _____  / /_  ___    ____ ___ \n"
    "  \__ \   / / / /  / /_/ / __  / /  ______  \__ \   / / / /  / ___/ / __/ / _ \  / __ `__ \ \n"
    " ___/ /  / /_/ /  / ____/ / /_/ /  /_____/ ___/ /  / /_/ /  (__  ) / /_  /  __/ / / / / / / \n"
    "/____/  /_____/  /_/      \____/          /____/   \__, /  /____/  \__/  \___/ /_/ /_/ /_/ \n"
    "                                                  /____/                                   \n"
    "                   Self–Detection based on Post–Jialbreak-System V1.0.0                    \n"
)


# ── 格式化器 ──


class _BoldHelpFormatter(click.HelpFormatter):
    """加粗小节标题，空行分隔"""

    def write_heading(self, heading):
        super().write_heading(click.style(heading, bold=True))

    def write_dl(self, rows, **kwargs):
        start = 0
        for i, (name, value) in enumerate(rows):
            if name == "" and value == "":
                if i > start:
                    super().write_dl(rows[start:i], **kwargs)
                self.buffer.append("\n")
                start = i + 1
        if start < len(rows):
            super().write_dl(rows[start:], **kwargs)


# ── Group ──


class OrderedGroup(click.Group):
    """按注册顺序显示命令，不使用字母排序。支持命令分组和 Banner。"""

    def __init__(self, name=None, commands=None, groups=None, banner=None, **attrs):
        super().__init__(name, commands, **attrs)
        self._groups = groups  # [(group_title, [cmd_names]), ...] 或 None
        self._banner = banner  # 顶层帮助横幅文本

    def list_commands(self, ctx):
        return list(self.commands.keys())

    def format_commands(self, ctx, formatter):
        if self._groups is None:
            rows = []
            names = self.list_commands(ctx)
            for i, name in enumerate(names):
                cmd = self.commands.get(name)
                if cmd is None or cmd.hidden:
                    continue
                rows.append((name, cmd.get_short_help_str()))
                if isinstance(cmd, click.Group):
                    rows.append(("", ""))
                    for sub_name, sub_cmd in cmd.commands.items():
                        if sub_cmd.hidden:
                            continue
                        rows.append((f"  {sub_name}", sub_cmd.get_short_help_str()))
                        if isinstance(sub_cmd, click.Group):
                            for s2_name, s2_cmd in sub_cmd.commands.items():
                                if not s2_cmd.hidden:
                                    rows.append((f"    {s2_name}", s2_cmd.get_short_help_str()))
                rows.append(("", ""))
            if rows:
                with formatter.section("Commands"):
                    formatter.write_dl(rows)
            return

        for group_title, cmd_names in self._groups:
            rows = []
            for name in cmd_names:
                if name in self.commands:
                    cmd = self.commands[name]
                    if not cmd.hidden:
                        rows.append((f"  {name}", cmd.get_short_help_str()))
            if rows:
                with formatter.section(f"  {group_title}"):
                    formatter.write_dl(rows)

    def format_help(self, ctx, formatter):
        if self._banner and ctx.parent is None:
            formatter.write(self._banner + "\n")
        super().format_help(ctx, formatter)

    def get_help(self, ctx):
        formatter = _BoldHelpFormatter(width=ctx.terminal_width)
        self.format_help(ctx, formatter)
        return formatter.getvalue() + "\n"
