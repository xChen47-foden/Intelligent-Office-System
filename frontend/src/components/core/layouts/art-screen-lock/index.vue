<template>
  <div class="layout-lock-screen">
    <div v-if="!isLock">
      <el-dialog v-model="visible" :width="370" :show-close="false" @open="handleDialogOpen">
        <div class="lock-content">
          <img 
            class="cover" 
            :src="getAvatarUrl(userInfo?.avatar)" 
            @error="handleAvatarError"
            :alt="userInfo.userName || '用户头像'"
          />
          <div class="username">{{ userInfo.userName }}</div>
          <el-form ref="formRef" :model="formData" :rules="rules" @submit.prevent="handleLock">
            <el-form-item prop="password">
              <el-input
                v-model="formData.password"
                type="password"
                :placeholder="$t(`lockScreen.lock.inputPlaceholder`)"
                :show-password="true"
                ref="lockInputRef"
                @keyup.enter="handleLock"
              >
                <template #suffix>
                  <el-icon class="cursor-pointer" @click="handleLock">
                    <Lock />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-button type="primary" class="lock-btn" @click="handleLock" v-ripple>
              {{ $t(`lockScreen.lock.btnText`) }}
            </el-button>
          </el-form>
        </div>
      </el-dialog>
    </div>

    <div class="unlock-content" v-else>
      <div class="box">
        <img 
          class="cover" 
          :src="getAvatarUrl(userInfo?.avatar)" 
          @error="handleAvatarError"
          :alt="userInfo.userName || '用户头像'"
        />
        <div class="username">{{ userInfo.userName }}</div>
        <el-form
          ref="unlockFormRef"
          :model="unlockForm"
          :rules="rules"
          @submit.prevent="handleUnlock"
        >
          <el-form-item prop="password">
            <el-input
              v-model="unlockForm.password"
              type="password"
              :placeholder="$t(`lockScreen.unlock.inputPlaceholder`)"
              :show-password="true"
              ref="unlockInputRef"
            >
              <template #suffix>
                <el-icon class="cursor-pointer" @click="handleUnlock">
                  <Unlock />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button type="primary" class="unlock-btn" @click="handleUnlock" v-ripple>
            {{ $t(`lockScreen.unlock.btnText`) }}
          </el-button>
          <el-button text class="login-btn" @click="toLogin">
            {{ $t(`lockScreen.unlock.backBtnText`) }}
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { Lock, Unlock } from '@element-plus/icons-vue'
  import type { FormInstance, FormRules } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'
  import { ElMessage } from 'element-plus'
  import mittBus from '@/utils/mittBus'
  import { useI18n } from 'vue-i18n'
  import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
  import { storeToRefs } from 'pinia'
  import defaultAvatar from '@/assets/img/avatar/avatar5.jpg'
  import { useSettingStore } from '@/store/modules/setting'
  
  const { t } = useI18n()
  const userStore = useUserStore()
  const settingStore = useSettingStore()
  const { info: userInfo, lockPassword, isLock } = storeToRefs(userStore)
  const { isDark } = storeToRefs(settingStore)
  
  // 头像URL处理函数
  const getAvatarUrl = (avatar?: string) => {
    if (!avatar) return defaultAvatar
    if (avatar.startsWith('http')) return avatar
    // 如果已经是/uploads/开头，直接使用，否则添加/uploads/前缀
    if (avatar.startsWith('/uploads/')) {
      return `${avatar}?t=${Date.now()}`
    }
    return `/uploads/${avatar}?t=${Date.now()}`
  }
  
  // 头像加载失败处理
  const handleAvatarError = (event: Event) => {
    const img = event.target as HTMLImageElement
    if (img.src !== defaultAvatar) {
      img.src = defaultAvatar
    }
  }

  const visible = ref(false)
  const formRef = ref<FormInstance>()
  const formData = reactive({
    password: ''
  })

  const rules = computed<FormRules>(() => ({
    password: [
      {
        required: true,
        message: t('lockScreen.lock.inputPlaceholder'),
        trigger: 'blur'
      }
    ]
  }))

  const unlockFormRef = ref<FormInstance>()
  const unlockForm = reactive({
    password: ''
  })

  // 添加禁用控制台的函数
  const disableDevTools = () => {
    // 禁用右键菜单
    document.addEventListener('contextmenu', (e) => {
      if (isLock.value) e.preventDefault()
    })

    // 禁用 F12 键
    document.addEventListener('keydown', (e) => {
      if (isLock.value && e.key === 'F12') {
        e.preventDefault()
      }
    })

    // 禁用 Ctrl+Shift+I/J/C
    document.addEventListener('keydown', (e) => {
      if (
        isLock.value &&
        e.ctrlKey &&
        e.shiftKey &&
        (e.key === 'I' ||
          e.key === 'i' ||
          e.key === 'J' ||
          e.key === 'j' ||
          e.key === 'C' ||
          e.key === 'c')
      ) {
        e.preventDefault()
      }
    })
  }

  watch(isLock, (newValue) => {
    if (newValue) {
      document.body.style.overflow = 'hidden'
      setTimeout(() => {
        unlockInputRef.value?.input?.focus()
      }, 100)
    } else {
      document.body.style.overflow = 'auto'
    }
  })

  onMounted(() => {
    mittBus.on('openLockScreen', openLockScreen)
    document.addEventListener('keydown', handleKeydown)

    if (isLock.value) {
      visible.value = true
      setTimeout(() => {
        unlockInputRef.value?.input?.focus()
      }, 100)
    }
    disableDevTools()
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })

  const verifyPassword = (inputPassword: string, storedPassword: string): boolean => {
    // 简化版本：直接比较明文密码
    return inputPassword === storedPassword
  }

  const handleUnlock = async () => {
    if (!unlockFormRef.value) return

    await unlockFormRef.value.validate((valid, fields) => {
      if (valid) {
        const isValid = verifyPassword(unlockForm.password, lockPassword.value)

        if (isValid) {
          try {
            userStore.setLockStatus(false)
            userStore.setLockPassword('')
            unlockForm.password = ''
            visible.value = false
          } catch (error) {
            console.error('更新store失败:', error)
          }
        } else {
          ElMessage.error(t('lockScreen.pwdError'))
        }
      } else {
        console.error('表单验证失败:', fields)
      }
    })
  }

  const handleKeydown = (event: KeyboardEvent) => {
    if (event.altKey && event.key.toLowerCase() === '¬') {
      event.preventDefault()
      visible.value = true
    }
  }

  const handleLock = async () => {
    if (!formRef.value) return

    await formRef.value.validate((valid, fields) => {
      if (valid) {
        // 简化版本：直接存储明文密码
        userStore.setLockStatus(true)
        userStore.setLockPassword(formData.password)
        visible.value = false
        formData.password = ''
      } else {
        console.error('表单验证失败:', fields)
      }
    })
  }

  const toLogin = () => {
    userStore.logOut()
  }

  const openLockScreen = () => {
    visible.value = true
  }

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
    document.body.style.overflow = 'auto'
  })

  // 添加输入框的 ref
  const lockInputRef = ref<any>(null)
  const unlockInputRef = ref<any>(null)

  // 修改处理方法
  const handleDialogOpen = () => {
    setTimeout(() => {
      lockInputRef.value?.input?.focus()
    }, 100)
  }
</script>

<style scoped lang="scss">
  .layout-lock-screen {
    .el-dialog {
      border-radius: 10px;
      
      :deep(.el-dialog__body) {
        padding: 20px;
      }
    }

    .lock-content {
      display: flex;
      flex-direction: column;
      align-items: center;

      .cover {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        background-color: #f5f5f5;
        
        &:hover {
          transform: scale(1.05);
        }
      }

      .username {
        margin: 15px 0;
        margin-top: 30px;
        font-size: 16px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        transition: color 0.3s ease;
      }

      .el-form {
        width: 90%;
      }

      .el-input {
        width: 100%;
        margin-top: 35px;
      }

      .lock-btn {
        width: 100%;
      }
    }

    .unlock-content {
      position: fixed;
      inset: 0;
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      background-color: #fff;
      background-image: url('@imgs/lock/lock_screen_1.png');
      background-size: cover;
      background-position: center;
      transition: all 0.3s ease-in-out;

      .box {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 320px;
        padding: 30px;
        background: rgb(255 255 255 / 90%);
        border-radius: 10px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;

        .cover {
          width: 64px;
          height: 64px;
          margin-top: 20px;
          border-radius: 50%;
          object-fit: cover;
          border: 2px solid rgba(255, 255, 255, 0.8);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: all 0.3s ease;
          background-color: #f5f5f5;
          
          &:hover {
            transform: scale(1.05);
          }
        }

        .username {
          margin: 15px 0;
          margin-top: 30px;
          font-size: 16px;
          font-weight: 500;
          color: #333;
          transition: color 0.3s ease;
        }

        .el-form {
          width: 100%;
          padding: 0 10px !important;
        }

        .el-input {
          margin-top: 20px;
        }

        .unlock-btn {
          width: 100%;
          margin-top: 10px;
        }

        .login-btn {
          display: block;
          margin: 10px auto;
          color: #333;
          transition: color 0.3s ease;

          &:hover {
            color: var(--el-color-primary) !important;
            background-color: transparent !important;
          }
        }
      }
    }
  }
</style>

<style lang="scss">
  // 深色模式全局样式
  html.dark {
    .layout-lock-screen {
      .el-dialog {
        background-color: var(--el-bg-color);
        border: 1px solid rgba(255, 255, 255, 0.1);
        
        :deep(.el-dialog__header) {
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
      }
      
      .lock-content {
        .username {
          color: rgba(255, 255, 255, 0.9);
        }
        
        .cover {
          border: 2px solid rgba(255, 255, 255, 0.2);
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
          background-color: #2a2a3a;
        }
      }
      
      .unlock-content {
        background-color: #070707;
        background-image: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        
        .box {
          background: rgba(30, 30, 40, 0.9);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.1);
          
          .cover {
            border: 2px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
            background-color: #2a2a3a;
          }
          
          .username {
            color: rgba(255, 255, 255, 0.9) !important;
          }
          
          .el-input {
            :deep(.el-input__wrapper) {
              background-color: rgba(255, 255, 255, 0.05);
              border-color: rgba(255, 255, 255, 0.2);
              
              &:hover {
                border-color: rgba(255, 255, 255, 0.3);
              }
              
              &.is-focus {
                border-color: var(--el-color-primary);
              }
            }
            
            :deep(.el-input__inner) {
              color: rgba(255, 255, 255, 0.9);
            }
          }
          
          .login-btn {
            color: rgba(255, 255, 255, 0.7) !important;
            
            &:hover {
              color: var(--el-color-primary) !important;
            }
          }
        }
      }
    }
  }
</style>
