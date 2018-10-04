import os
import pathlib
from os.path import join
from typing import TypeVar, Generic, Sequence

from canvasapi.exceptions import Unauthorized
from canvasapi.file import File
from canvasapi.folder import Folder

from .utils import *

T = TypeVar('T')


class FileTree(Generic[T]):
    def __init__(self, path: str, folders: 'Sequence[FileTree[T]]', files: Sequence[T]):
        self.path = path
        self.folders: 'Sequence[FileTree[T]]' = folders
        self.files: Sequence[T] = files


def build_canvas_file_tree(base, folder: Folder) -> FileTree[File]:
    folders = list(map(lambda subfolder: build_canvas_file_tree(join(base, subfolder.name), subfolder), folder.get_folders()))
    files = list(folder.get_files())
    return FileTree(base, folders, files)


def length_file_tree(folder: FileTree) -> int:
    return sum(map(length_file_tree, folder.folders)) + len(folder.files)


def pull_file_tree(directory, tree):
    pathlib.Path(join(directory, tree.path)).mkdir(parents=True, exist_ok=True)

    for file in tree.files:
        file_path = join(join(directory, tree.path), file.filename)

        canvas_mtime = unix_time_seconds(file.modified_at_date.replace(tzinfo=pytz.utc))

        if not os.path.exists(file_path) or canvas_mtime > os.stat(file_path).st_mtime:
            file.download(file_path)
            atime = os.stat(file_path).st_atime
            os.utime(file_path, (atime, canvas_mtime))

    for subtree in tree.folders:
        pull_file_tree(directory, subtree)


def pull_all_files(directory, course: Course):
    top_level_folder = next(folder for folder in course.get_folders() if folder.parent_folder_id is None)
    try:
        tree = build_canvas_file_tree('.', top_level_folder)
        get_outputter().poutput_verbose('Detected ' + str(length_file_tree(tree)) + ' files.')
        pull_file_tree(directory, tree)
    except Unauthorized:
        get_outputter().poutput('Not authorized to access this course\'s files')
