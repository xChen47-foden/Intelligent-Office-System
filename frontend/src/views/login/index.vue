<template>
  <div class="login">
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
          <h3 class="title">{{ $t('login.title') }}</h3>
          <p class="sub-title">{{ $t('login.subTitle') }}</p>
          <el-form
            ref="formRef"
            :model="formData"
            :rules="rules"
            @keyup.enter="handleSubmit"
            style="margin-top: 25px"
          >
            <el-form-item prop="username">
              <el-input v-model.trim="formData.username" :placeholder="$t('login.placeholder[0]')" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                :placeholder="$t('login.placeholder[1]')"
                v-model.trim="formData.password"
                :type="showPassword ? 'text' : 'password'"
                radius="8px"
                autocomplete="off"
              >
                <template #suffix>
                  <el-icon @click="showPassword = !showPassword" style="cursor:pointer;">
                    <component :is="showPassword ? 'View' : 'Hide'" />
                  </el-icon>
                </template>
              </el-input>
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
            <div class="drag-verify">
              <div class="drag-verify-content" :class="{ error: !isPassing && isClickPass }">
                <ArtDragVerify
                  ref="dragVerify"
                  v-model:value="isPassing"
                  :width="width < 500 ? 328 : 438"
                  :text="$t('login.sliderText')"
                  :textColor="isDark ? 'rgba(255, 255, 255, 0.8)' : 'var(--art-gray-800)'"
                  :successText="$t('login.sliderSuccessText')"
                  :progressBarBg="getCssVariable('--el-color-primary')"
                  :background="isDark ? 'rgba(255, 255, 255, 0.1)' : 'var(--art-gray-200)'"
                  :handlerBg="isDark ? 'rgba(255, 255, 255, 0.2)' : 'var(--art-main-bg-color)'"
                  @pass="onPass"
                />
              </div>
              <p class="error-text" :class="{ 'show-error-text': !isPassing && isClickPass }">{{
                $t('login.placeholder[2]')
              }}</p>
            </div>

            <div class="forget-password">
              <el-checkbox v-model="formData.rememberPassword">{{
                $t('login.rememberPwd')
              }}</el-checkbox>
              <router-link to="/forget-password">{{ $t('login.forgetPwd') }}</router-link>
            </div>

            <div style="margin-top: 30px">
              <el-button
                class="login-btn"
                type="primary"
                @click="handleSubmit"
                :loading="loading"
                v-ripple
              >
                {{ $t('login.btnText') }}
              </el-button>
            </div>

            <div class="footer">
              <p>
                {{ $t('login.noAccount') }}
                <router-link to="/register">{{ $t('login.register') }}</router-link>
              </p>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, computed } from 'vue'
  import AppConfig from '@/config'
  import { ElMessage, ElNotification } from 'element-plus'
  import type { FormInstance, FormRules } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'
  import { HOME_PAGE } from '@/router/routesAlias'
  import { ApiStatus } from '@/utils/http/status'
  import { getCssVariable } from '@/utils/colors'

  import { View, Hide } from '@element-plus/icons-vue'
  import { asyncRoutes } from '@/router/routes/asyncRoutes'
  import { useRouter } from 'vue-router'
  import type { RouteRecordRaw } from 'vue-router'
  import { useI18n } from 'vue-i18n'
  import { storeToRefs } from 'pinia'
  import { useSettingStore } from '@/store/modules/setting'
  import { themeAnimation } from '@/utils/theme/animation'
  import { useWindowSize } from '@vueuse/core'
  import ArtDragVerify from '@/components/core/forms/ArtDragVerify.vue'
  import LoginLeftView from '@/components/core/views/login/LoginLeftView.vue'

  const userStore = useUserStore()
  const settingStore = useSettingStore()
  const { isDark } = storeToRefs(settingStore)
  const router = useRouter()
  const isPassing = ref(false)
  const isClickPass = ref(false)

  const systemName = AppConfig.systemInfo.name
  const formRef = ref<FormInstance>()
  
  // 响应式宽度
  const { width } = useWindowSize()

  const formData = reactive({
    username: '',
    password: '',
    department: '',
    rememberPassword: true
  })

  const rules = computed<FormRules>(() => ({
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    department: [{ required: true, message: '请选择部门', trigger: 'change' }]
  }))

  const loading = ref(false)

  const showPassword = ref(false)
  const dragVerify = ref()

  const onPass = () => {}

  const handleSubmit = async () => {
    if (!formRef.value) return

    await formRef.value.validate(async (valid) => {
      if (valid) {
        if (!isPassing.value) {
          isClickPass.value = true
          return
        }

        loading.value = true

        const params = {
          username: formData.username,
          password: formData.password,
          department: formData.department
        }

        try {
          const res = await UserService.login(params)
          console.log('🔐 登录响应:', res)
          console.log('🔍 响应详情:', {
            code: res.code,
            codeType: typeof res.code,
            ApiStatus_success: ApiStatus.success,
            data: res.data
          })
          
          // 支持多种成功状态码格式  
          const codeStr = String(res.code)
          const isSuccess = codeStr === '0' || codeStr === '200' || res.code === ApiStatus.success
          
          if (isSuccess) {
            console.log('✅ 登录成功，开始设置状态')
            
            // 设置token和登录状态
            await userStore.setToken(res.data.token)
            console.log('🎫 Token设置完成')
            
            await userStore.setLoginStatus(true)
            console.log('👤 登录状态设置完成')
            
            // 获取用户信息
            try {
            const userInfoRes = await UserService.getUserInfo()
              console.log('👤 用户信息响应:', userInfoRes)
              const userCodeStr = String(userInfoRes.code)
              const userInfoSuccess = userCodeStr === '0' || userCodeStr === '200' || userInfoRes.code === ApiStatus.success
              
              if (userInfoSuccess) {
              userStore.setUserInfo(userInfoRes.data)
                await userStore.saveUserData()
                console.log('📄 用户信息获取并保存完成')
              } else {
                console.warn('用户信息获取失败，但继续登录流程')
              }
            } catch (userInfoError) {
              console.warn('获取用户信息失败，但登录成功:', userInfoError)
            }
            
            showLoginSuccessNotice()
            
            console.log('🔄 准备跳转到工作台')
            console.log('📍 当前路由:', router.currentRoute.value.path)
            console.log('🎯 目标路由: /workbench')
            
            // 直接使用 window.location 强制跳转
            console.log('🚀 使用强制跳转')
            window.location.href = '#/workbench'
          } else {
            ElMessage.error(res.msg || '登录失败')
          }
        } catch (e: any) {
          console.error('登录失败:', e)
          console.error('错误详情:', {
            message: e?.message,
            response: e?.response,
            status: e?.response?.status,
            data: e?.response?.data
          })
          
          // 显示更详细的错误信息
          let errorMsg = '网络异常或服务器错误'
          if (e?.response?.data?.msg) {
            errorMsg = e.response.data.msg
          } else if (e?.response?.data?.detail) {
            errorMsg = e.response.data.detail
          } else if (e?.message) {
            errorMsg = e.message
          }
          
          ElMessage.error(errorMsg)
        } finally {
          loading.value = false
          resetDragVerify()
        }
      }
    })
  }

  // 重置拖拽验证
  const resetDragVerify = () => {
    dragVerify.value.reset()
  }

  // 登录成功提示
  const showLoginSuccessNotice = () => {
    setTimeout(() => {
      ElNotification({
        title: '登录成功',
        type: 'success',
        duration: 2500,
        zIndex: 10000,
        message: '登录成功，欢迎使用系统！'
      })
    }, 150)
  }



  // 切换主题
  import { useTheme } from '@/composables/useTheme'
  import { UserService } from '@/api/usersApi'
  import { SystemThemeEnum } from '@/enums/appEnum'

  const toggleTheme = () => {
    let { LIGHT, DARK } = SystemThemeEnum
    useTheme().switchThemeStyles(settingStore.systemThemeType === LIGHT ? DARK : LIGHT)
  }
</script>

<style lang="scss" scoped>
  @use './index';
</style>
