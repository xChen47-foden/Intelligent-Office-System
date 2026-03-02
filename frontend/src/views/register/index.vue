<template>
  <div class="login register">
    <div class="left-wrap">
      <LoginLeftView></LoginLeftView>
    </div>
    <div class="right-wrap">
      <!-- 主题切换按钮 -->
      <div class="theme-toggle" @click="themeAnimation($event)">
        <div class="btn theme-btn">
          <i class="iconfont-sys">{{ isDark ? '&#xe6b5;' : '&#xe725;' }}</i>
        </div>
      </div>

      <div class="header">
        <svg class="icon" aria-hidden="true">
          <use xlink:href="#iconsys-zhaopian-copy"></use>
        </svg>
        <h1>{{ systemName }}</h1>
      </div>
      <div class="login-wrap">
        <div class="form">
          <h3 class="title">注册新账号</h3>
          <p class="sub-title">欢迎注册智能办公助手系统</p>
          <el-form ref="formRef" :model="formData" :rules="rules" label-position="top">
            <el-form-item prop="username">
              <el-input
                v-model.trim="formData.username"
                placeholder="请输入用户名"
              />
            </el-form-item>

            <el-form-item prop="contact">
              <el-input
                v-model.trim="formData.contact"
                placeholder="请输入邮箱"
              />
            </el-form-item>

            <el-form-item prop="captcha">
              <el-row :gutter="8">
                <el-col :span="16">
                  <el-input
                    v-model.trim="formData.captcha"
                    placeholder="请输入验证码"
                  />
                </el-col>
                <el-col :span="8">
                  <el-button @click="sendCaptcha" :disabled="captchaCountdown > 0">
                    {{ captchaCountdown > 0 ? `${captchaCountdown}s后重发` : '获取验证码' }}
                  </el-button>
                </el-col>
              </el-row>
            </el-form-item>

            <el-form-item prop="department" label="部门">
              <el-select v-model="formData.department" placeholder="请选择部门">
                <el-option label="技术部" value="技术部" />
                <el-option label="市场部" value="市场部" />
                <el-option label="人事部" value="人事部" />
                <el-option label="财务部" value="财务部" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model.trim="formData.password"
                placeholder="请输入密码"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="off"
              >
                <template #suffix>
                  <el-icon @click="showPassword = !showPassword" style="cursor:pointer;">
                    <component :is="showPassword ? 'View' : 'Hide'" />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model.trim="formData.confirmPassword"
                placeholder="请确认密码"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="off"
                @keyup.enter="register"
              >
                <template #suffix>
                  <el-icon @click="showConfirmPassword = !showConfirmPassword" style="cursor:pointer;">
                    <component :is="showConfirmPassword ? 'View' : 'Hide'" />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="agreement">
              <el-checkbox v-model="formData.agreement">
                我已阅读并同意
                <router-link
                  style="color: var(--el-color-primary); text-decoration: none"
                  to="/privacy-policy"
                  >《隐私政策》</router-link
                >
              </el-checkbox>
            </el-form-item>

            <div style="margin-top: 15px">
              <el-button
                class="register-btn"
                type="primary"
                @click="register"
                :loading="loading"
                v-ripple
              >
                注册
              </el-button>
            </div>

            <div class="footer">
              <p>
                已有账号？
                <router-link to="/login">去登录</router-link>
              </p>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue'
  import AppConfig from '@/config'
  import { ElMessage } from 'element-plus'
  import type { FormInstance, FormRules } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { View, Hide } from '@element-plus/icons-vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  import { storeToRefs } from 'pinia'
  import { useSettingStore } from '@/store/modules/setting'
  import { themeAnimation } from '@/utils/theme/animation'
  import LoginLeftView from '@/components/core/views/login/LoginLeftView.vue'

  const { t } = useI18n()

  const router = useRouter()
  const settingStore = useSettingStore()
  const { isDark } = storeToRefs(settingStore)
  const formRef = ref<FormInstance>()

  const systemName = AppConfig.systemInfo.name
  const loading = ref(false)

  const formData = reactive({
    username: '',
    password: '',
    confirmPassword: '',
    contact: '',
    captcha: '',
    department: '',
    agreement: false
  })

  const showPassword = ref(false)
  const showConfirmPassword = ref(false)

  const validatePass = (rule: any, value: string, callback: any) => {
    if (value === '') {
      callback(new Error('请输入密码'))
    } else {
      if (formData.confirmPassword !== '') {
        formRef.value?.validateField('confirmPassword')
      }
      callback()
    }
  }

  const validatePass2 = (rule: any, value: string, callback: any) => {
    if (value === '') {
      callback(new Error('请确认密码'))
    } else if (value !== formData.password) {
      callback(new Error('两次输入的密码不一致'))
    } else {
      callback()
    }
  }

  const rules = reactive<FormRules>({
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '用户名长度为3-20位', trigger: 'blur' }
    ],
    contact: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { validator: (rule: any, value: string, callback: any) => {
          const emailReg = /^[\w-\.]+@[\w-]+(\.[\w-]+)+$/;
          if (!emailReg.test(value)) {
            callback(new Error('请输入正确的邮箱'));
          } else {
            callback();
          }
        }, trigger: 'blur' }
    ],
    captcha: [
      { required: true, message: '请输入验证码', trigger: 'blur' }
    ],
    department: [
      { required: true, message: '请选择部门', trigger: 'change' }
    ],
    password: [
      { required: true, validator: validatePass, trigger: 'blur' },
      { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
    ],
    confirmPassword: [{ required: true, validator: validatePass2, trigger: 'blur' }],
    agreement: [
      {
        validator: (rule: any, value: boolean, callback: any) => {
          if (!value) {
            callback(new Error('请阅读并同意隐私政策'))
          } else {
            callback()
          }
        },
        trigger: 'change'
      }
    ]
  })

  // 注册逻辑：调用后端注册接口，校验验证码，注册成功存入数据库
  const register = async () => {
    if (!formRef.value) return
    try {
      await formRef.value.validate()
      loading.value = true
      // 调用后端注册接口
      const res = await axios.post('/api/register', {
        username: formData.username,
        password: formData.password,
        contact: formData.contact,
        captcha: formData.captcha,
        department: formData.department
      })
      if (res.data.code === 0) {
        ElMessage.success('注册成功')
        console.log('准备跳转')
        window.location.href = '/workbench'
      } else {
        ElMessage.error(res.data.msg || '注册失败')
      }
    } catch (error: any) {
      console.error('注册失败:', error)
      // FastAPI 的 HTTPException 返回格式为 {detail: "错误信息"}
      if (error?.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else if (error?.response?.data?.msg) {
        ElMessage.error(error.response.data.msg)
      } else if (error?.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('注册失败，请检查网络连接或稍后重试')
      }
    } finally {
      loading.value = false
    }
  }

  // 验证码相关
  const captchaCountdown = ref(0)
  let captchaTimer: any = null
  const sendCaptcha = async () => {
    if (!formData.contact) {
      ElMessage.warning('请先输入邮箱')
      return
    }
    // 前端格式校验
    const emailReg = /^[\w-\.]+@[\w-]+(\.[\w-]+)+$/;
    if (!emailReg.test(formData.contact)) {
      ElMessage.warning('请输入正确的邮箱')
      return
    }
    try {
      // 调用后端接口发送验证码
      const res = await axios.post('/api/send-captcha', { contact: formData.contact })
      if (res.data.code === 0) {
        ElMessage.success('验证码已发送')
        captchaCountdown.value = 60
        captchaTimer = setInterval(() => {
          captchaCountdown.value--
          if (captchaCountdown.value <= 0) {
            clearInterval(captchaTimer)
          }
        }, 1000)
      } else {
        ElMessage.error(res.data.msg || '验证码发送失败')
      }
    } catch (error: any) {
      if (error?.response?.data) {
        ElMessage.error(error.response.data.error || error.response.data.msg || '验证码发送失败')
        console.error('后端返回:', error.response.data)
      } else {
        ElMessage.error('验证码发送失败')
        console.error(error)
      }
    }
  }
</script>

<style lang="scss" scoped>
  @use '../login/index' as login;
  @use './index' as register;
</style>
