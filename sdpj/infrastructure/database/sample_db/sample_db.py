"""SampleDB 瀹炵幇.

瀹炵幇 SampleDBInterface 鎺ュ彛,鎻愪緵妫€娴嬫牱鏈暟鎹簱鐨勫畬鏁村姛鑳?
"""


from .repositories import DatasetRepository, SampleRepository
from .session import SampleDBSessionManager


class SampleDB:
    """妫€娴嬫牱鏈暟鎹簱瀹炵幇.

    瀹炵幇 SampleDBInterface 瀹氫箟鐨勬墍鏈夎兘鍔?
    DataProcessor 鏄敮涓€璋冪敤鏂?
    """

    def __init__(self, session_manager: SampleDBSessionManager) -> None:
        """鍒濆鍖?SampleDB.

        Args:
            session_manager: 鏁版嵁搴撲細璇濈鐞嗗櫒

        """
        self.session_manager = session_manager

    # ==================== 鏁版嵁闆嗙骇鑳藉姏 ====================

    async def create_dataset(
        self, name: str, risk_type: str, resource_id: int | None = None,
    ) -> int:
        """鍒涘缓妫€娴嬫暟鎹泦.

        Args:
            name: 鏁版嵁闆嗗悕绉?
            risk_type: 瀹夊叏椋庨櫓绫诲瀷
            resource_id: 瀵瑰簲 UserDB Resource 琛ㄧ殑 resource_id(鍐呯疆鏁版嵁闆嗕负 None)

        Returns:
            鏂板垱寤烘暟鎹泦鐨勬暟鎹泦 ID

        Raises:
            ValueError: 鏁版嵁闆嗗悕绉板湪绯荤粺鍐呴噸澶嶆椂鎷掔粷鍐欏叆

        """
        async with self.session_manager.session() as session:
            repo = DatasetRepository(session)
            dataset = await repo.create(name, risk_type, resource_id)
            await session.commit()
            return dataset.dataset_id

    async def delete_dataset(self, dataset_id: int) -> bool:
        """鍒犻櫎妫€娴嬫暟鎹泦.

        鍚庣疆鏉′欢:
        - 绾ц仈鍒犻櫎璇ユ暟鎹泦涓嬬殑鎵€鏈夋牱鏈?婊¤冻澶栭敭瀹屾暣鎬?

        Args:
            dataset_id: 鏁版嵁闆?ID

        Returns:
            鍒犻櫎缁撴灉(True 琛ㄧず鎴愬姛)

        """
        async with self.session_manager.session() as session:
            repo = DatasetRepository(session)
            result = await repo.delete(dataset_id)
            await session.commit()
            return result

    async def get_all_datasets(self) -> list[dict]:
        """鏌ヨ鏁版嵁闆嗗垪琛?

        Returns:
            鍏ㄩ儴鏁版嵁闆嗗厓淇℃伅鍒楄〃

        """
        async with self.session_manager.session() as session:
            repo = DatasetRepository(session)
            return await repo.get_all_with_sample_count()

    async def get_dataset_by_name(self, name: str) -> dict | None:  # noqa: D102
        async with self.session_manager.session() as session:
            repo = DatasetRepository(session)
            dataset = await repo.get_by_name(name)
            if dataset is None:
                return None
            return {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "risk_type": dataset.risk_type,
                "resource_id": dataset.resource_id,
                "created_at": dataset.created_at,
            }

    async def get_sample_count_by_dataset(self, dataset_id: int) -> int:  # noqa: D102
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            return await repo.count_by_dataset(dataset_id)

    async def get_dataset_by_id(self, dataset_id: int) -> dict | None:
        """鎸?ID 鏌ヨ鍗曚釜鏁版嵁闆?

        Args:
            dataset_id: 鏁版嵁闆?ID

        Returns:
            鏁版嵁闆嗗厓淇℃伅瀛楀吀,涓嶅瓨鍦ㄦ椂杩斿洖 None

        """
        async with self.session_manager.session() as session:
            repo = DatasetRepository(session)
            dataset = await repo.get_by_id(dataset_id)
            if dataset is None:
                return None
            return {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "risk_type": dataset.risk_type,
                "resource_id": dataset.resource_id,
                "created_at": dataset.created_at,
            }

    async def get_datasets_by_risk_type(self, risk_type: str) -> list[dict]:
        """鎸夊畨鍏ㄩ闄╃被鍨嬬瓫閫夋暟鎹泦.

        Args:
            risk_type: 瀹夊叏椋庨櫓绫诲瀷

        Returns:
            鍖归厤鐨勬暟鎹泦鍒楄〃

        """
        async with self.session_manager.session() as session:
            repo = DatasetRepository(session)
            datasets = await repo.get_by_risk_type(risk_type)
            return [
                {
                    "dataset_id": ds.dataset_id,
                    "name": ds.name,
                    "risk_type": ds.risk_type,
                    "resource_id": ds.resource_id,
                    "created_at": ds.created_at,
                }
                for ds in datasets
            ]

    # ==================== 鏍锋湰绾ц兘鍔?====================

    async def add_sample(self, subtype: str, poc: str, dataset_id: int) -> int:
        """娣诲姞妫€娴嬫牱鏈埌鎸囧畾鏁版嵁闆?

        Args:
            subtype: 椋庨櫓鍏蜂綋瀛愮被 ST
            poc: 婕忔礊姒傚康楠岃瘉鏁版嵁 PoC
            dataset_id: 鎵€灞炴暟鎹泦 ID

        Returns:
            鏂板垱寤烘牱鏈殑鏍锋湰 ID

        Raises:
            ValueError: 鎵€灞炴暟鎹泦 ID 涓嶅瓨鍦ㄦ椂鎷掔粷鍐欏叆

        """
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            sample = await repo.create(subtype, poc, dataset_id)
            await session.commit()
            return sample.sample_id

    async def bulk_add_samples(
        self, records: list[tuple[str, str, int]], batch_size: int = 5000,
    ) -> int:
        """鎵归噺娣诲姞妫€娴嬫牱鏈?

        Args:
            records: [(subtype, poc, dataset_id), ...] 鍒楄〃
            batch_size: 姣忔壒鎻愪氦鐨勮鏁?

        Returns:
            鎴愬姛鎻掑叆鐨勬€昏鏁?

        """
        from .models import DetectionSample  # noqa: PLC0415

        inserted = 0
        async with self.session_manager.session() as session:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                objects = [DetectionSample(subtype=r[0], poc=r[1], dataset_id=r[2]) for r in batch]
                session.add_all(objects)
                await session.flush()
                inserted += len(batch)
            await session.commit()
        return inserted

    async def bulk_insert_samples(
        self, records: list[tuple[str, str, int]], batch_size: int = 5000,
    ) -> int:
        """鎵归噺鎻掑叆妫€娴嬫牱鏈?鍘熺敓 SQL,缁曡繃 ORM 灞?.

        Args:
            records: [(subtype, poc, dataset_id), ...] 鍒楄〃
            batch_size: 姣忔壒鎻愪氦鐨勮鏁?

        Returns:
            鎴愬姛鎻掑叆鐨勬€昏鏁?

        """
        from sqlalchemy import insert as sql_insert  # noqa: PLC0415

        from .models import DetectionSample  # noqa: PLC0415

        inserted = 0
        async with self.session_manager.session() as session:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                await session.execute(
                    sql_insert(DetectionSample),
                    [{"subtype": r[0], "poc": r[1], "dataset_id": r[2]} for r in batch],
                )
                await session.flush()
                inserted += len(batch)
            await session.commit()
        return inserted

    async def delete_sample(self, sample_id: int) -> bool:
        """鍒犻櫎妫€娴嬫牱鏈?

        Args:
            sample_id: 鏍锋湰 ID

        Returns:
            鍒犻櫎缁撴灉(True 琛ㄧず鎴愬姛)

        """
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            result = await repo.delete(sample_id)
            await session.commit()
            return result

    async def delete_samples_by_dataset(self, dataset_id: int) -> int:
        """鍒犻櫎鎸囧畾鏁版嵁闆嗕笅鐨勬墍鏈夋牱鏈?

        Args:
            dataset_id: 鏁版嵁闆?ID

        Returns:
            鍒犻櫎鐨勮鏁?

        """
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            count = await repo.delete_by_dataset(dataset_id)
            await session.commit()
            return count

    async def get_samples_by_dataset(self, dataset_id: int) -> list[dict]:
        """鎸夋暟鎹泦 ID 鏌ヨ鎵€鏈夋牱鏈?

        Args:
            dataset_id: 鏁版嵁闆?ID

        Returns:
            璇ユ暟鎹泦涓嬪叏閮ㄦ牱鏈垪琛?

        """
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            samples = await repo.get_by_dataset(dataset_id)
            return [
                {
                    "sample_id": s.sample_id,
                    "subtype": s.subtype,
                    "poc": s.poc,
                    "dataset_id": s.dataset_id,
                    "created_at": s.created_at,
                }
                for s in samples
            ]

    async def get_samples_by_risk_type(self, risk_type: str) -> list[dict]:
        """鎸夊畨鍏ㄩ闄╃被鍨嬫煡璇㈡墍鏈夋牱鏈?鍗曟 JOIN 鏌ヨ,鏇夸唬 N+1).

        Args:
            risk_type: 瀹夊叏椋庨櫓绫诲瀷

        Returns:
            鍖归厤鐨勬墍鏈夋牱鏈垪琛?

        """
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            samples = await repo.get_by_risk_type(risk_type)
            return [
                {
                    "sample_id": s.sample_id,
                    "subtype": s.subtype,
                    "poc": s.poc,
                    "dataset_id": s.dataset_id,
                    "created_at": s.created_at,
                }
                for s in samples
            ]

    async def get_sample_by_id(self, sample_id: int) -> dict | None:
        """鎸?ID 鏌ヨ鍗曟潯鏍锋湰.

        Args:
            sample_id: 鏍锋湰 ID

        Returns:
            鍗曟潯鏍锋湰璇︽儏瀛楀吀,涓嶅瓨鍦ㄦ椂杩斿洖 None

        """
        async with self.session_manager.session() as session:
            repo = SampleRepository(session)
            sample = await repo.get_by_id(sample_id)
            if sample is None:
                return None
            return {
                "sample_id": sample.sample_id,
                "subtype": sample.subtype,
                "poc": sample.poc,
                "dataset_id": sample.dataset_id,
                "created_at": sample.created_at,
            }

    # ==================== 绯荤粺鍏冩暟鎹兘鍔?====================

    async def get_system_meta(self, key: str) -> str | None:
        """鏌ヨ绯荤粺鍏冩暟鎹?

        Args:
            key: 鍏冩暟鎹敭

        Returns:
            鍏冩暟鎹€?涓嶅瓨鍦ㄦ椂杩斿洖 None

        """
        from .models import SystemMeta  # noqa: PLC0415

        async with self.session_manager.session() as session:
            from sqlalchemy import select  # noqa: PLC0415

            result = await session.execute(select(SystemMeta.value).where(SystemMeta.key == key))
            return result.scalar_one_or_none()

    async def set_system_meta(self, key: str, value: str) -> None:
        """璁剧疆绯荤粺鍏冩暟鎹?upsert).

        Args:
            key: 鍏冩暟鎹敭
            value: 鍏冩暟鎹€?

        """
        from .models import SystemMeta  # noqa: PLC0415

        async with self.session_manager.session() as session:
            from sqlalchemy import select  # noqa: PLC0415

            result = await session.execute(select(SystemMeta).where(SystemMeta.key == key))
            existing = result.scalar_one_or_none()
            if existing is not None:
                existing.value = value
            else:
                session.add(SystemMeta(key=key, value=value))
            await session.commit()
