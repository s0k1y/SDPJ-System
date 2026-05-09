我提交的任务是一个动态检测任务，要求重构PoC池，被测数据集只有一个，我认为它应该是先重构PoC池，重构完成后先执行静态检测，静态检测结束后再执行动态检测


### 任务组: 995904bc-fa02-4f8e-868b-32872ed9f32a
- 目标模型: deepseek-v4-pro
- 状态: running
- 当前阶段: poc_selecting（PoC池构建/选择阶段）

#### 子任务1: PoC池构建
- 任务ID: poc_995904bc-fa02-4f8e-868b-32872ed9f32a
- 状态: running

#### 子任务2: 用户数据集检测
- 任务ID: b6c01482-8232-4753-a133-b041e71070a4
- 状态: running
- 数据集: user_datasets/username/test (ID:18)



---

## 后端数据库日志 


| 时间 | 类别 | 级别 | 模块 | 用户 | 事件 | 描述 |
|------|------|------|------|------|------|------|
| 2026-05-08 17:21:45.122 | runtime | info | StateScheduler |  | state_transition | 状态转移: idle → detecting (触发: start_detection) |
| 2026-05-08 17:21:45.143 | operation | info | user | 1 | start_detection | start_detection |
| 2026-05-08 17:21:45.143 | runtime | info | StateScheduler |  | detection_queued | 任务组 995904bc-fa02-4f8e-868b-32872ed9f32a 已入队, 共 1 个子任务 |
| 2026-05-08 17:21:46.774 | runtime | info | StateScheduler |  | task_started | 子任务 b6c01482-8232-4753-a133-b041e71070a4 开始执行 |
| 2026-05-08 17:21:46.774 | runtime | info | StateScheduler |  | detection_exec | 开始执行检测: type=dynamic, model=deepseek-v4-pro, dataset_ids=[18], jailbreak_ids=None, force_refresh=False, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:23:49.211 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=100, total=22276, found=13, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:24:55.994 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=200, total=22276, found=13, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:26:24.890 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=300, total=22276, found=14, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:27:19.560 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=400, total=22276, found=14, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:28:43.047 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=500, total=22276, found=14, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:29:59.231 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=600, total=22276, found=15, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:31:24.389 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=700, total=22276, found=16, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:32:42.124 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=800, total=22276, found=17, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:34:24.943 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=900, total=22276, found=20, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:35:25.686 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1000, total=22276, found=20, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:37:08.489 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1100, total=22276, found=21, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:38:27.086 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1200, total=22276, found=22, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:39:35.962 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1300, total=22276, found=22, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:41:10.098 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1400, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:42:16.520 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1500, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:42:50.262 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1600, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:43:29.320 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1700, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:44:29.677 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1800, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:45:30.677 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=1900, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:46:54.238 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2000, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:48:01.183 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2100, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:48:35.561 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2200, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:49:41.955 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2300, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:50:13.880 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2400, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:50:44.253 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2500, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:51:24.248 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2600, total=22276, found=23, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:52:24.383 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2700, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:03.083 | operation | info | user | 1 | login | login |
| 2026-05-08 17:53:23.625 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2800, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:23.626 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=2900, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:23.629 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3000, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:23.629 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3100, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:42.311 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3200, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:42.314 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3300, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:53:42.314 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3400, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:54:40.510 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3500, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:54:54.670 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3600, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:55:54.682 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3700, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:55:54.683 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3800, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:56:05.635 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=3900, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:56:22.717 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4000, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:56:39.773 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4100, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:57:17.495 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4200, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:57:17.498 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4300, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:57:17.501 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4400, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:57:31.520 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4500, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:57:49.079 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4600, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:57:49.081 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4700, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:58:10.616 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4800, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:58:25.977 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=4900, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:58:38.469 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5000, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:59:02.514 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5100, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:59:02.516 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5200, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:59:17.070 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5300, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 17:59:42.525 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5400, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:00:39.551 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5500, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:00:53.596 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5600, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:01:10.076 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5700, total=22276, found=24, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:02:18.072 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5800, total=22276, found=25, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:04:01.266 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=5900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:04:15.908 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:05:16.664 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:05:16.667 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:05:28.689 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:06:29.664 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:06:41.655 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:07:00.474 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:07:20.663 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:07:41.243 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:08:41.660 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=6900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:09:21.324 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:09:32.517 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:10:32.667 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:10:43.757 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:10:43.761 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:10:58.885 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:11:19.409 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:11:19.414 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:11:51.462 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:11:51.464 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=7900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:11:51.464 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:11:51.468 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:12:58.131 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:12:58.133 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:12:58.136 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:13:39.560 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:13:58.079 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:14:34.586 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:14:34.587 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:14:46.712 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=8900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:14:58.643 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:12.948 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:28.856 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:28.859 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:28.861 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:44.007 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:57.161 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:15:57.165 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:16:25.922 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:16:40.808 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=9900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:16:55.439 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:17:15.189 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:17:15.192 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:17:30.237 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:18:18.730 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:19:26.125 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:19:43.354 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:19:54.735 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:21:19.944 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:22:54.515 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=10900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:23:07.533 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:23:28.983 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:23:28.986 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:23:44.022 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:24:04.963 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:24:19.450 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:24:33.590 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:25:02.186 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:25:15.961 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:26:16.664 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=11900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:27:01.692 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:27:15.537 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:27:47.021 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:27:56.531 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:27:56.534 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:13.523 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:36.768 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:36.771 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:48.791 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:48.794 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=12900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:48.795 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:28:48.797 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:29:08.091 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:29:08.092 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:29:08.095 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:29:29.221 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:29:41.792 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:30:32.228 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:30:32.232 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:30:44.589 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=13900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:30:56.280 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:08.112 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:25.486 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:25.490 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:25.491 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14400, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:40.641 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14500, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:56.668 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14600, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:31:56.672 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14700, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:32:14.062 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14800, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:32:29.933 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=14900, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:32:41.189 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15000, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:32:53.511 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15100, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:32:53.515 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15200, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:05.390 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15300, total=22276, found=26, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.274 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15400, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.275 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15500, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.278 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15600, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.280 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15700, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.282 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15800, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.283 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=15900, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.285 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16000, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.286 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16100, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.287 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16200, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.289 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16300, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.291 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16400, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.291 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16500, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.293 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16600, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.296 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16700, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.297 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16800, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.299 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=16900, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.300 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17000, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.302 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17100, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.303 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17200, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.304 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17300, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.306 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17400, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.307 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17500, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.309 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17600, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.310 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17700, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.312 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17800, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.314 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=17900, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.316 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18000, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.318 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18100, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.321 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18200, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.322 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18300, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.322 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18400, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.326 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18500, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.327 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18600, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.329 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18700, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.330 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18800, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.332 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=18900, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.333 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19000, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.335 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19100, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.336 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19200, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.337 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19300, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.339 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19400, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.340 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19500, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.341 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19600, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.342 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19700, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.344 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19800, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.344 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=19900, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:33:45.347 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=20000, total=22276, found=27, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:36:59.445 | runtime | info | StateScheduler |  | poc_progress | PoC进度回调: processed=20100, total=22276, found=40, group_id=995904bc-fa02-4f8e-868b-32872ed9f32a |
| 2026-05-08 18:36:59.540 | error | error | StateScheduler |  | DetectionError | 子任务 b6c01482-8232-4753-a133-b041e71070a4 异常: 任务组ID '995904bc-fa02-4f8e-868b-32872ed9f32a' 不存在 |
| 2026-05-08 18:36:59.543 | runtime | info | StateScheduler |  | state_transition | 状态转移: detecting → idle (触发: task_finished) |
| 2026-05-08 18:37:03.293 | runtime | info | StateScheduler |  | orphan_cleanup | 清理孤儿任务组 995904bc-fa02-4f8e-868b-32872ed9f32a, 移除 1 个任务 |
| 2026-05-09 01:16:05.939 | operation | info | user | 1 | query_datasets | query_datasets |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:28:06.125 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:31:37.551 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:36:24.089 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:37:25.483 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:37:25.483 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:37:25.483 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:37:25.483 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:37:25.484 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:37:25.484 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:37:25.485 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:44:43.826 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:44:43.826 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:44:43.826 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:44:43.827 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:44:43.827 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:44:43.828 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:44:43.828 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:49:11.343 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:49:11.343 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:49:11.344 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:49:11.344 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:49:11.344 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:49:11.344 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:49:11.345 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:50:38.203 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:50:49.903 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:50:49.904 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:50:49.904 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:50:49.904 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:50:49.904 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:50:49.904 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:50:49.904 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |
| 2026-05-09 01:51:26.211 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:51:37.911 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-Z1-Flash |
| 2026-05-09 01:51:37.912 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:51:37.912 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4-Flash-250414 |
| 2026-05-09 01:51:37.912 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: GLM-4.7-Flash |
| 2026-05-09 01:51:37.913 | runtime | info | StateScheduler |  | adapter_restored | 启动时恢复适配器: deepseek-v4-pro |
| 2026-05-09 01:51:37.913 | runtime | info | StateScheduler |  | consumer_started | 后台任务消费者已启动 (间隔=2.0s, 并发=3) |
| 2026-05-09 01:51:37.913 | runtime | info | StateScheduler |  | adapters_restored | 启动时共恢复 5 个适配器 |

