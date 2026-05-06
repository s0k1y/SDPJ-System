## ADDED Requirements

### Requirement: 资源授权清单展示
系统 SHALL 在权限管理页面展示当前登录用户拥有的所有受控资源列表，选中资源后展示该资源的访问控制清单（每条含访问控制项ID、被授权用户ID/用户名）。

#### Scenario: 用户查看自己的资源列表
- **WHEN** 用户进入权限管理页面
- **THEN** 系统调用 `GET /api/users/resources` 获取当前用户拥有的资源列表并展示

#### Scenario: 用户查看某资源的授权清单
- **WHEN** 用户在资源列表中选中某个资源
- **THEN** 系统调用 `POST /api/users/dac`（operation=list，传入resource_id）获取该资源的访问控制清单并展示

#### Scenario: 用户无受控资源
- **WHEN** 用户进入权限管理页面且该用户无任何受控资源
- **THEN** 系统显示"暂无私有资源"提示

#### Scenario: 资源无授权条目
- **WHEN** 用户选中某个资源且该资源无任何访问控制条目
- **THEN** 系统显示"暂无授权记录"提示

### Requirement: 访问权授予
系统 SHALL 允许资源拥有者通过权限管理页面授予其他用户对该资源的读权限。

#### Scenario: 成功授予访问权
- **WHEN** 用户在选中资源后点击"授权"按钮，输入被授权用户ID，确认授权
- **THEN** 系统调用 `POST /api/users/dac`（operation=grant，传入resource_id和target_user_id），成功后刷新授权清单并提示"授权成功"

#### Scenario: 授予访问权失败-非资源拥有者
- **WHEN** 非资源拥有者尝试授予访问权
- **THEN** 系统提示"仅资源拥有者可授予访问权"

#### Scenario: 授予访问权失败-用户已拥有访问权
- **WHEN** 用户尝试对已拥有访问权的用户再次授权
- **THEN** 系统提示"该用户已拥有访问权"

### Requirement: 访问权移除
系统 SHALL 允许资源拥有者通过权限管理页面移除已授予的读权限。

#### Scenario: 成功移除访问权
- **WHEN** 用户在授权清单中点击某条访问控制项的"移除"按钮并确认
- **THEN** 系统调用 `POST /api/users/dac`（operation=revoke，传入acl_id），成功后刷新授权清单并提示"已移除"

#### Scenario: 移除访问权失败-非资源拥有者
- **WHEN** 非资源拥有者尝试移除访问权
- **THEN** 系统提示"仅资源拥有者可移除访问权"

### Requirement: 访问权判定
系统 SHALL 在权限管理页面提供访问权判定功能，显示当前用户对指定资源是否具备访问权。

#### Scenario: 检查访问权
- **WHEN** 用户输入资源ID并点击"检查权限"
- **THEN** 系统调用 `GET /api/users/dac/check`（传入resource_id），显示"有访问权"或"无访问权"
