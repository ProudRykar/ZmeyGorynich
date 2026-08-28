"""Тонкая обёртка вокруг системного git через subprocess.

Никаких внешних зависимостей — только стандартный модуль subprocess.
Все команды выполняются в корне git-репозитория, который определяется
через `git rev-parse --show-toplevel`.
"""
import os
import subprocess


class GitError(RuntimeError):
    pass


def find_repo_root(start):
    """Возвращает абсолютный путь к корню репозитория или None."""
    try:
        out = _run(["rev-parse", "--show-toplevel"], cwd=start, capture=True)
    except GitError:
        return None
    return out.strip() or None


def _run(args, cwd, capture=True, check=False):
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise GitError("git не найден в системе: " + str(exc))

    out = proc.stdout or ""
    err = proc.stderr or ""

    if check and proc.returncode != 0:
        msg = (err or out).strip() or "git завершился с ошибкой"
        raise GitError(msg)

    return out


class GitRepo:
    """Обёртка над git-репозиторием в заданном каталоге."""

    def __init__(self, root):
        self.root = root

    @classmethod
    def discover(cls, start):
        root = find_repo_root(start)
        return cls(root) if root else None

    def _run(self, args, check=False):
        return _run(args, cwd=self.root, check=check)

    # --- информация ---

    def branch(self):
        out = self._run(["rev-parse", "--abbrev-ref", "HEAD"], check=False).strip()
        if out in ("", "HEAD"):
            return "(detached HEAD)"
        return out

    def status(self):
        """Возвращает список словарей с изменёнными файлами.

        Каждый элемент: {path, staged (bool), untracked (bool), x, y, rename}.
        """
        raw = self._run(
            ["status", "--porcelain=v1", "-z"], check=False)
        files = []
        parts = raw.split("\0")

        i = 0
        while i < len(parts):
            entry = parts[i]
            if len(entry) < 3:
                i += 1
                continue

            x = entry[0]
            y = entry[1]
            rest = entry[3:]

            path = rest
            rename = None
            if "R" in (x, y) or "C" in (x, y):
                # для переименований/копий формат: orig\0new
                if i + 1 < len(parts):
                    rename = rest
                    path = parts[i + 1]
                    i += 1

            files.append({
                "path": path,
                "rename": rename,
                "x": x,
                "y": y,
                "staged": x not in (" ", "?"),
                "untracked": x == "?",
            })
            i += 1

        return files

    # --- индексация ---

    def stage(self, path):
        self._run(["add", "--", path], check=True)

    def unstage(self, path):
        self._run(["restore", "--staged", "--", path], check=True)

    def stage_all(self):
        self._run(["add", "-A"], check=True)

    def unstage_all(self):
        self._run(["restore", "--staged", "-A"], check=True)

    # --- история ---

    def commit(self, message, all_=False):
        args = ["commit"]
        if all_:
            args.append("-a")
        args += ["-m", message]
        return self._run(args, check=False).strip()

    def push(self, remote="origin"):
        return self._run(["push", remote], check=False).strip()

    def pull(self, remote="origin"):
        return self._run(["pull", remote], check=False).strip()
