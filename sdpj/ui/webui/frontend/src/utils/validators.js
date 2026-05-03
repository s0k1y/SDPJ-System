/**
 * Element Plus 表单验证规则
 */

// 用户名：3-20位字母数字下划线
export const usernameRules = [
  { required: true, message: '请输入用户名', trigger: 'blur' },
  { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' },
  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
]

// 密码：至少6位
export const passwordRules = [
  { required: true, message: '请输入密码', trigger: 'blur' },
  { min: 6, max: 32, message: '密码长度为 6-32 个字符', trigger: 'blur' }
]

// 确认密码
export function confirmPasswordRule(getPassword) {
  return [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== getPassword()) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 必填项
export const requiredRule = (message) => [
  { required: true, message, trigger: 'blur' }
]

// 正整数
export const positiveIntRule = (message) => [
  { required: true, message, trigger: 'blur' },
  { type: 'number', min: 1, message: '请输入正整数', trigger: 'blur' }
]
