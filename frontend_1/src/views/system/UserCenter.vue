<template>
    <div class="user-center-page">
      <el-row :gutter="24" class="user-center-row">
        <!-- 左侧个人信息卡片 -->
        <el-col :span="7" :xs="24" class="user-info-col">
          <el-card class="user-info-card">
            <div class="avatar-wrap">
              <div class="avatar-bg">
                <el-avatar
                  :size="80"
                  class="avatar-img"
                  :src="getAvatarUrl(userInfo.avatar)"
                  :key="userInfo.avatar + avatarTimestamp"
                />
              </div>
              <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="onAvatarChange" />
              <el-button size="small" @click="triggerAvatarUpload" style="margin-bottom:8px;">上传头像</el-button>
              <el-button size="small" @click="onRandomAvatar" style="margin-bottom:8px;">随机头像</el-button>
              <div class="user-name">{{ userInfo.userName }}</div>
              <div class="user-role-badge">
                <span class="role-badge">{{ userInfo.roles && userInfo.roles.length ? userInfo.roles.join(',') : '普通用户' }}</span>
              </div>
            </div>
            <el-descriptions :column="1" border class="desc-table">
              <el-descriptions-item label="账号">{{ userInfo.userName }}</el-descriptions-item>
              <el-descriptions-item label="ID">{{ String(userInfo.userId ?? '') }}</el-descriptions-item>
            </el-descriptions>
            <el-divider />
            <el-button type="primary" @click="showPwdDialog = true" style="width: 100%;">修改密码</el-button>
          </el-card>
        </el-col>
        <!-- 右侧表单区 -->
        <el-col :span="17" :xs="24" class="user-form-col">
          <el-card class="user-form-card">
            <h3 class="section-title">基本信息</h3>
            <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" class="user-form">
              <el-form-item label="姓名" prop="realName">
                <el-input v-model="form.realName" class="round-input" />
              </el-form-item>
              <el-form-item label="昵称" prop="nickName">
                <el-input v-model="form.nickName" class="round-input" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="onSave">保存</el-button>
                <el-button @click="onReset">重置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
          <el-card class="user-form-card preferences-card">
            <h3 class="section-title">偏好设置</h3>
            <el-form label-width="80px" class="user-form">
              <el-form-item label="主题">
                <el-select v-model="preferences.theme" class="round-input">
                  <el-option label="自动" value="auto">
                    <span class="theme-dot auto"></span>自动
                  </el-option>
                  <el-option label="明亮" value="light">
                    <span class="theme-dot light"></span>明亮
                  </el-option>
                  <el-option label="暗黑" value="dark">
                    <span class="theme-dot dark"></span>暗黑
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="onSavePreferences">保存</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
      <!-- 修改密码弹窗 -->
      <el-dialog v-model="showPwdDialog" title="修改密码" width="400px" class="pwd-dialog">
        <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="80px">
          <el-form-item label="原密码" prop="oldPwd">
            <el-input v-model="pwdForm.oldPwd" type="password" class="round-input" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPwd">
            <el-input v-model="pwdForm.newPwd" type="password" class="round-input" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPwd">
            <el-input v-model="pwdForm.confirmPwd" type="password" class="round-input" />
          </el-form-item>
        </el-form>
        <template #footer>
          <div class="dialog-footer-center">
            <el-button @click="showPwdDialog = false">取消</el-button>
            <el-button type="primary" @click="onPwdSave">保存</el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, onMounted, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'
  import { storeToRefs } from 'pinia'
  import { UserService } from '@/api/usersApi'
  import { useTheme } from '@/composables/useTheme'
  import { SystemThemeEnum } from '@/enums/appEnum'
  import defaultAvatar from '@/assets/img/avatar/avatar5.jpg'
  
  const userStore = useUserStore()
  const { info } = storeToRefs(userStore)
  const userInfo = info.value
  
  // 添加响应式时间戳
  const avatarTimestamp = ref(Date.now())
  
  // 头像URL获取函数
  const getAvatarUrl = (avatar: string) => {
    if (!avatar) return defaultAvatar
    if (avatar.startsWith('http')) return avatar
    // 如果已经是/uploads/开头，直接使用，否则添加/uploads/前缀
    if (avatar.startsWith('/uploads/')) {
      return `${avatar}?t=${avatarTimestamp.value}`
    }
    return `/uploads/${avatar}?t=${avatarTimestamp.value}`
  }
  
  // 更新头像时间戳
  const updateAvatarTimestamp = () => {
    avatarTimestamp.value = Date.now()
  }
  
  // 自动刷新用户信息
  const { switchThemeStyles } = useTheme()
  onMounted(async () => {
    const res = await UserService.getUserInfo()
    if (res && res.code == 0 && res.data) {
      const user = {
        userId: Number(res.data.userId) || 0,
        userName: res.data.userName || res.data.username || '',
        roles: res.data.roles || [],
        buttons: res.data.buttons || [],
        realName: res.data.realName || '',
        nickName: res.data.nickName || '',
        avatar: res.data.avatar || '',
      }
      userStore.setUserInfo(user)
      form.realName = user.realName
      form.nickName = user.nickName
      preferences.theme = res.data.theme || 'auto'
      // 不在初始化时强制切换主题，保持用户当前的主题状态
      // switchThemeStyles((res.data.theme || 'auto') as SystemThemeEnum)
    }
    // 初始化完成后，允许主题切换
    isInitialized = true
  })
  
  // 基本信息表单
  const formRef = ref()
  const form = reactive({
    realName: '',
    nickName: '',
  })
  const rules = {
    realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  }
  const onSave = async () => {
    const res = await UserService.updateUserInfo({
      realName: form.realName,
      nickName: form.nickName
    })
    if (res && res.code == 0) {
      ElMessage.success('保存成功')
      // 保存后刷新用户信息
      const userRes = await UserService.getUserInfo()
      if (userRes && res.code == 0 && userRes.data) {
        const user = {
          userId: Number(userRes.data.userId) || 0,
          userName: userRes.data.userName || userRes.data.username || '',
          roles: userRes.data.roles || [],
          buttons: userRes.data.buttons || [],
          realName: userRes.data.realName || '',
          nickName: userRes.data.nickName || '',
          avatar: userRes.data.avatar || '',
        }
        userStore.setUserInfo(user)
        form.realName = user.realName
        form.nickName = user.nickName
      }
    }
  }
  const onReset = () => {
    form.realName = userInfo.realName || ''
    form.nickName = userInfo.nickName || ''
  }
  
  // 偏好设置
  const preferences = reactive({
    theme: 'auto'
  })
  
  // 主题切换逻辑 - 只在用户主动改变时触发，避免初始化时重置主题
  let isInitialized = false
  watch(
    () => preferences.theme,
    (val) => {
      // 只有在初始化完成后才触发主题切换
      if (isInitialized) {
      switchThemeStyles(val as SystemThemeEnum)
      }
    }
  )
  
  // 修改密码弹窗
  const showPwdDialog = ref(false)
  const pwdFormRef = ref()
  const pwdForm = reactive({
    oldPwd: '',
    newPwd: '',
    confirmPwd: ''
  })
  const pwdRules = {
    oldPwd: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
    newPwd: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
    confirmPwd: [
      { required: true, message: '请确认新密码', trigger: 'blur' },
      { validator: (rule: any, value: string, callback: any) => {
          if (value !== pwdForm.newPwd) {
            callback(new Error('两次输入密码不一致'))
          } else {
            callback()
          }
        }, trigger: 'blur' }
    ]
  }
  const onPwdSave = () => {
    if (pwdForm.newPwd !== pwdForm.confirmPwd) {
      ElMessage.error('两次输入密码不一致')
      return
    }
    ElMessage.success('密码修改成功（模拟）')
    showPwdDialog.value = false
    pwdForm.oldPwd = ''
    pwdForm.newPwd = ''
    pwdForm.confirmPwd = ''
  }
  
  // 偏好设置保存
  const onSavePreferences = async () => {
    const res = await UserService.updatePreferences({
      theme: preferences.theme,
      language: 'zh' // 添加默认语言参数
    })
    if (res && res.code == 0) {
      ElMessage.success('偏好设置已保存')
      // 立即应用主题切换
      switchThemeStyles(preferences.theme as SystemThemeEnum)
    }
  }
  
  const avatarInput = ref<HTMLInputElement | null>(null)
  const triggerAvatarUpload = () => {
    (avatarInput.value as HTMLInputElement).click()
  }
  const onAvatarChange = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    const res = await UserService.uploadAvatar(file)
    if (res && res.code == 0 && res.data?.avatar) {
      userInfo.avatar = res.data.avatar
      // 更新全局用户状态
      userStore.setUserInfo({
        userId: userInfo.userId || 0,
        userName: userInfo.userName || '',
        roles: userInfo.roles || [],
        buttons: userInfo.buttons || [],
        realName: userInfo.realName || '',
        nickName: userInfo.nickName || '',
        avatar: res.data.avatar
      })
      updateAvatarTimestamp()  // 更新时间戳
      ElMessage.success('头像上传成功')
    } else {
      ElMessage.error(res?.msg || '头像上传失败')
    }
  }
  const onRandomAvatar = async () => {
    const res = await UserService.generateAvatar()
    if (res && res.code == 0 && res.data && res.data.avatar) {
      userInfo.avatar = res.data.avatar
      // 更新全局用户状态
      userStore.setUserInfo({
        userId: userInfo.userId || 0,
        userName: userInfo.userName || '',
        roles: userInfo.roles || [],
        buttons: userInfo.buttons || [],
        realName: userInfo.realName || '',
        nickName: userInfo.nickName || '',
        avatar: res.data.avatar
      })
      updateAvatarTimestamp()  // 更新时间戳
      ElMessage.success('已切换为随机头像')
    } else {
      ElMessage.error(res?.msg || '生成随机头像失败')
    }
  }
  </script>
  
  <style scoped>
  .user-center-page {
    padding: 32px;
    min-height: 100vh;
    background: var(--el-bg-color-page);
  }
  .user-center-row {
    flex-wrap: wrap;
  }
  .user-info-col {
    min-width: 320px;
  }
  .user-info-card {
    text-align: center;
    margin-bottom: 24px;
    border-radius: 18px;
    box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
    background: var(--el-bg-color);
    border: none;
  }
  .avatar-wrap {
    margin-bottom: 18px;
    margin-top: 8px;
  }
  .avatar-bg {
    display: flex;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 100%);
    border-radius: 50%;
    width: 96px;
    height: 96px;
    margin: 0 auto 10px auto;
    box-shadow: 0 2px 12px 0 rgba(129,140,248,0.18);
  }
  .avatar-img {
    border: 3px solid #fff;
    box-shadow: 0 2px 8px 0 rgba(129,140,248,0.12);
  }
  .user-name {
    font-size: 22px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 2px;
    color: var(--el-text-color-primary);
  }
  .user-role-badge {
    margin-bottom: 10px;
  }
  .role-badge {
    display: inline-block;
    background: linear-gradient(90deg, #6366f1 0%, #818cf8 100%);
    color: #fff;
    font-size: 13px;
    border-radius: 12px;
    padding: 2px 14px;
    font-weight: 500;
    letter-spacing: 1px;
  }
  .desc-table {
    margin-bottom: 10px;
    background: var(--el-bg-color);
    border-radius: 10px;
  }
  .user-form-col {
    min-width: 320px;
  }
  .user-form-card {
    margin-bottom: 28px;
    border-radius: 16px;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.06);
    border: none;
    background: var(--el-bg-color);
  }
  .section-title {
    margin-bottom: 18px;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  .user-form {
    max-width: 500px;
  }
  .round-input :deep(.el-input__wrapper),
  .round-input :deep(.el-select__wrapper) {
    border-radius: 18px !important;
    min-height: 38px;
  }
      .preferences-card {
      margin-top: 24px;
    }
    .theme-dot {
      display: inline-block;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      margin-right: 8px;
      vertical-align: middle;
    }
    .theme-dot.auto {
      background: linear-gradient(135deg, #818cf8 0%, #fbbf24 100%);
    }
    .theme-dot.light {
      background: #fbbf24;
    }
    .theme-dot.dark {
      background: #6366f1;
    }
    .pwd-dialog :deep(.el-dialog__body) {
      padding-bottom: 0;
    }
  .dialog-footer-center {
    text-align: center;
  }
  @media (max-width: 900px) {
    .user-center-row {
      flex-direction: column;
    }
    .user-info-col, .user-form-col {
      min-width: 0;
      width: 100%;
    }
    .user-info-card, .user-form-card {
      margin-bottom: 18px;
    }
  }
  </style>
  