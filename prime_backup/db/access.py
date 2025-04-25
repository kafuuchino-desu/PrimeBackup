import contextlib
from pathlib import Path
from typing import Optional, ContextManager

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import Session

from prime_backup.config.config import Config
from prime_backup.db import db_constants
from prime_backup.db.migration import DbMigration
from prime_backup.db.session import DbSession
from prime_backup.types.hash_method import HashMethod
from prime_backup.config.database_config import DatabaseConfig


class DbAccess:
	__engine: Optional[Engine] = None
	__db_file_path: Optional[Path] = None

	__hash_method: Optional[HashMethod] = None

	@classmethod
	def init(cls, create: bool, migrate: bool):
		"""
		"""
		config = Config.get()
		db_dir = config.storage_path
		if create:
			db_dir.mkdir(parents=True, exist_ok=True)

		db_path = db_dir / db_constants.DB_FILE_NAME
		cls.__engine = create_engine('sqlite:///' + str(db_path))
		cls.__db_file_path = db_path

		migration = DbMigration(cls.__engine, db_dir, db_path, config.temp_path)
		migration.check_and_migrate(create=create, migrate=migrate)

		cls.sync_hash_method()

	@classmethod
	def shutdown(cls):
		if (engine := cls.__engine) is not None:
			engine.dispose()
			cls.__engine = None

	@classmethod
	def sync_hash_method(cls):
		with cls.open_session() as session:
			hash_method_str = str(session.get_db_meta().hash_method)
		try:
			cls.__hash_method = HashMethod[hash_method_str]
		except KeyError:
			raise ValueError('invalid hash method {!r} in db meta'.format(hash_method_str)) from None

	@classmethod
	def __ensure_engine(cls) -> Engine:
		if cls.__engine is None:
			raise RuntimeError('engine unavailable')
		return cls.__engine

	@classmethod
	def __ensure_not_none(cls, value):
		if value is None:
			raise RuntimeError('db not is not initialized yet')
		return value

	@classmethod
	def get_db_file_path(cls) -> Path:
		return cls.__ensure_not_none(cls.__db_file_path)

	@classmethod
	def get_hash_method(cls) -> HashMethod:
		return cls.__ensure_not_none(cls.__hash_method)

	@classmethod
	@contextlib.contextmanager
	def open_session(cls) -> ContextManager['DbSession']:
		with Session(cls.__ensure_engine()) as session, session.begin():
			#ensure we uses in-memory temp storage if configured: https://www.sqlite.org/pragma.html#pragma_temp_store
			if DatabaseConfig.use_memory_tempstore:
				session.execute(text('PRAGMA temp_store = 2'))
			yield DbSession(session, cls.__db_file_path)

	@classmethod
	@contextlib.contextmanager
	def enable_echo(cls) -> ContextManager[None]:
		engine = cls.__ensure_engine()
		engine.echo = True
		try:
			yield
		finally:
			engine.echo = False
