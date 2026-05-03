PrivateConfigManager / 用户私有检测配置管理模块
具体职责:

# 私有检测配置 CRUD
1. 创建用户私有检测配置
   - 输入:所属用户ID、检测配置内容(被测大模型标识、待选用数据集标识、静态/动态算法类型及参数等)
   - 输出:tuple[bool, int | None]，成功时返回新创建的私有检测配置ID(同时作为 UserCenter 中对应受控资源的资源ID)，失败时返回 None
   - 后置条件:对应受控资源已在 UserCenter 登记,ACL 承载点已建立;配置内容已落盘到 UserCenter 维护的私有配置内容存储中
   - 触发场景:用户创建一份私有检测配置文件(对应 1.spec.md 功能 3.1.1.2);该配置是 1.spec.md 功能 1.3(选择检测数据集)的输入之一
   - 调用下层:UserCenter 的「登记受控资源」建立 ACL 承载点;UserCenter 的「写入用户私有检测配置内容」持久化配置内容;LLMRegistry 的「按标识校验大模型是否可用」确认被测大模型可用
   - 不负责的边界:不做权限判定(由 DACManager 在调用前完成);不做配置内容在 C-S 链路上的加解密(由 SecureCommManager 完成)

2. 读取用户私有检测配置
   - 输入:私有检测配置ID
   - 输出:该私有检测配置的完整内容
   - 触发场景:用户查看私有检测配置;系统在启动检测前加载用户选择的检测配置(对应 1.spec.md 功能 1.1 / 1.2 / 1.3 / 3.1.1.2)
   - 调用下层:UserCenter 的「读取用户私有检测配置内容」
   - 不负责的边界:不做权限判定(由 DACManager 在调用前完成)

3. 修改用户私有检测配置
   - 输入:私有检测配置ID、更新后的配置内容
   - 输出:修改结果
   - 触发场景:用户编辑已有的私有检测配置(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:UserCenter 的「更新用户私有检测配置内容」写入新内容;若修改涉及被测大模型标识,追加调用 LLMRegistry 的「按标识校验大模型是否可用」确认有效

4. 删除用户私有检测配置
   - 输入:私有检测配置ID
   - 输出:删除结果
   - 后置条件:对应受控资源及其相关 ACL 条目、私有检测配置内容均由下层级联清理
   - 触发场景:用户删除某份私有检测配置(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:UserCenter 的「移除受控资源」

5. 列出用户的私有检测配置清单
   - 输入:用户ID
   - 输出:该用户拥有的私有检测配置清单
   - 触发场景:用户在私有配置管理界面查看自己的配置列表(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:UserCenter 的「按拥有者查询资源清单」(筛选资源类型为"私有检测配置")

5-1. 查询可用检测数据集清单
   - 输入:无
   - 输出:全部可用检测数据集元信息列表(包含系统内置数据集与用户上传的私有数据集)
   - 触发场景:用户在启动检测前浏览可用检测数据集清单(对应 1.spec.md 功能 1.3)
   - 调用下层:DataProcessor 的「查询检测数据集清单」
   - 不负责的边界:不做数据集内容的加载与解析(由 DataProcessor 完成);不做调用方分页/排序/按业务属性过滤

# 私有大模型适配器管理
6. 上传用户私有大模型适配器
   - 输入:适配器文件内容、目标大模型标识、所属用户ID
   - 输出:上传结果(含新登记的大模型标识与对应受控资源ID)
   - 后置条件:适配器已由 LLMRegistry 入库并注册到内存注册表;对应受控资源已在 UserCenter 登记,ACL 承载点已建立
   - 触发场景:用户上传私有大模型适配器(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:DataProcessor 的「预校验上传文件格式」做文件格式预校验;LLMRegistry 的「注册用户上传的私有大模型」完成入库注册;UserCenter 的「登记受控资源」建立 ACL 承载点

7. 移除用户私有大模型适配器
   - 输入:目标大模型标识、所属资源ID
   - 输出:移除结果
   - 后置条件:对应适配器从 LLMRegistry 与 LLMAdapterLib 移除;对应受控资源及其相关 ACL 条目由下层级联清理
   - 触发场景:用户移除私有大模型适配器(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:LLMRegistry 的「注销用户移除的私有大模型」;UserCenter 的「移除受控资源」

# 私有数据集管理
8. 上传用户私有数据集
   - 输入:数据集元信息(名称、安全风险类型)、样本条目清单、所属用户ID
   - 输出:新创建的数据集ID(同时作为 UserCenter 中对应受控资源的资源ID)及各新增样本ID
   - 后置条件:数据集已由 DataProcessor 写入 SampleDB;对应受控资源已在 UserCenter 登记,ACL 承载点已建立
   - 触发场景:用户上传私有数据集(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:DataProcessor 的「预校验上传文件格式」做文件格式预校验;DataProcessor 的「导入用户私有数据集」写入样本;UserCenter 的「登记受控资源」建立 ACL 承载点

9. 移除用户私有数据集
   - 输入:数据集ID
   - 输出:移除结果
   - 后置条件:对应数据集由 DataProcessor 在 SampleDB 中删除；对应受控资源及 ACL 条目由下层级联清理
   - 触发场景:用户移除私有数据集(对应 1.spec.md 功能 3.1.1.2)
   - 调用下层:DataProcessor 的「移除私有数据集」；追加调用 UserCenter 的「移除受控资源」

# 私有检测配置的导入导出
10. 导出用户私有检测配置
    - 输入:私有检测配置ID、目标文件格式
    - 输出:可供用户下载的私有检测配置文件内容
    - 触发场景:用户导出私有检测配置以备份或跨账号复用(对应 1.spec.md 功能 3.1.1.2)
    - 调用下层:DataProcessor 的「结构化数据的序列化与反序列化」
    - 不负责的边界:不做 C-S 链路上的加密(由 SecureCommManager 完成)

11. 导入用户私有检测配置
    - 输入:用户上传的私有检测配置文件内容、所属用户ID
    - 输出:新创建的私有检测配置ID
    - 触发场景:用户导入此前导出的私有检测配置文件(对应 1.spec.md 功能 3.1.1.2)
    - 调用下层:DataProcessor 的「预校验上传文件格式」与「结构化数据的序列化与反序列化」;UserCenter 的「登记受控资源」建立 ACL 承载点;UserCenter 的「写入用户私有检测配置内容」持久化解析出的配置内容;若配置涉及被测大模型,追加调用 LLMRegistry 的「按标识校验大模型是否可用」

# 接口契约
13. 通过 PrivateConfigManagerInterface 对外暴露上述能力,被 StateScheduler 调用(符合 4.模型依赖关系图.puml 中 StateScheduler → PrivateConfigManager 边)

不需要的:[做权限判定(由 DACManager 完成),做 C-S 链路上的加解密传输(由 SecureCommManager 完成),做密码/凭据管理(由 AccountManager / UserCenter 完成),做大模型 API 的实际调用(由 SDPJDetector 经 LLMService 完成),做适配器/数据集/配置文件的格式校验具体实现(由 UtilsLib 完成),做检测合规判断(由 SDPJDetector 完成)]

依赖模块:DataProcessor,UserCenter,LLMRegistry,调用接口:DataProcessorInterface,UserCenterInterface,LLMRegistryInterface
应实现接口:PrivateConfigManagerInterface
被依赖模块:StateScheduler
技术细节:(暂定)
