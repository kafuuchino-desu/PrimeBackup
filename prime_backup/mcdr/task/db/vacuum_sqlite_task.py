import time
from pathlib import Path
from typing import Optional

from mcdreforged.api.all import *
from typing_extensions import override

from prime_backup.action.vacuum_sqlite_action import VacuumSqliteAction
from prime_backup.mcdr.task.basic_task import HeavyTask
from prime_backup.mcdr.text_components import TextComponents


class VacuumSqliteTask(HeavyTask[None]):
	def __init__(self, source: CommandSource, target_path: Optional[Path] = None, use_memory_tempfile: Optional[bool] = False):
		super().__init__(source)
		self.target_path = target_path
		self.use_memory_tempfile = use_memory_tempfile

	@property
	@override
	def id(self) -> str:
		return 'db_vacuum'

	@override
	def run(self) -> None:
		self.reply_tr('start')
		t = time.time()
		diff = VacuumSqliteAction(self.target_path, self.use_memory_tempfile).run()
		cost = time.time() - t
		self.reply_tr(
			'done',
			TextComponents.number(f'{cost:.2f}s'),
			TextComponents.file_size(diff.before),
			TextComponents.file_size(diff.after),
			TextComponents.file_size(diff.diff, color=RColor.dark_green) if diff.diff != 0 else RText('-0B', RColor.dark_green),
			TextComponents.percent(diff.after, diff.before),
		)
