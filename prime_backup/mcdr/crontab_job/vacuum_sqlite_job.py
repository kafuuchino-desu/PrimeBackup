from typing import TYPE_CHECKING

from apscheduler.schedulers.base import BaseScheduler
from typing_extensions import override

from prime_backup.config.config_common import CrontabJobSetting
from prime_backup.config.database_config import CompactDatabaseConfig
from prime_backup.mcdr.crontab_job import CrontabJobId
from prime_backup.mcdr.crontab_job.basic_job import BasicCrontabJob
from prime_backup.mcdr.task.db.vacuum_sqlite_task import VacuumSqliteTask

if TYPE_CHECKING:
	from prime_backup.mcdr.task_manager import TaskManager


class VacuumSqliteJob(BasicCrontabJob):
	def __init__(self, scheduler: BaseScheduler, task_manager: 'TaskManager'):
		super().__init__(scheduler, task_manager)
		self.config: CompactDatabaseConfig = self._root_config.database.compact
		self.use_memory_tempfile = self._root_config.database.vacuum_use_memory_tempfile

	@property
	@override
	def id(self) -> CrontabJobId:
		return CrontabJobId.vacuum_sqlite

	@property
	@override
	def job_config(self) -> CrontabJobSetting:
		return self.config

	@override
	def run(self):
		self.run_task_with_retry(VacuumSqliteTask(self.get_command_source(), use_memory_tempfile= self.use_memory_tempfile), True).report()
