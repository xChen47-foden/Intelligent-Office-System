<template>
  <div class="login register">
    <div class="left-wrap">
      <LoginLeftView></LoginLeftView>
    </div>
    <div class="right-wrap">
      <div class="header">
        <svg class="icon" aria-hidden="true">
          <use xlink:href="#iconsys-zhaopian-copy"></use>
        </svg>
        <h1>{{ systemName }}</h1>
      </div>
      <div class="login-wrap">
        <div class="form">
          <h3 class="title">{{ $t('forgetPassword.title') }}</h3>
          <p class="sub-title">{{ $t('forgetPassword.subTitle') }}</p>
          <div class="input-wrap">
            <span class="input-label" v-if="showInputLabel">邮箱</span>
            <el-input :placeholder="$t('forgetPassword.placeholder')" v-model.trim="contact" />
          </div>
          <div class="input-wrap" style="margin-top: 15px;">
            <span class="input-label">验证码</span>
            <div style="display: flex; align-items: center; margin-top: 8px;">
              <el-input placeholder="请输入验证码" v-model.trim="captcha" style="flex: 1;" />
              <el-button
                style="margin-left: 10px; min-width: 100px;"
                :disabled="countdown > 0 || !contact"
                @click="sendCaptcha"
                type="primary"
              >
                {{ countdown > 0 ? `${countdown}s后重发` : '获取验证码' }}
              </el-button>
            </div>
          </div>
          <div class="input-wrap" style="margin-top: 15px">
            <span class="input-label">新密码</span>
            <el-input placeholder="请输入新密码" v-model.trim="newPassword" show-password />
          </div>
          <div class="input-wrap" style="margin-top: 15px">
            <span class="input-label">确认新密码</span>
            <el-input placeholder="请再次输入新密码" v-model.trim="confirmPassword" show-password />
          </div>

          <div style="margin-top: 15px">
            <el-button
              class="login-btn"
              type="primary"
              @click="register"
              :loading="loading"
              v-ripple
            >
              {{ $t('forgetPassword.submitBtnText') }}
            </el-button>
          </div>

          <div style="margin-top: 15px">
            <el-button class="back-btn" plain @click="toLogin">
              {{ $t('forgetPassword.backBtnText') }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import AppConfig from '@/config'
  import { ElMessage } from 'element-plus'
  import { UserService } from '@/api/usersApi'
  import api from '@/utils/http'
  import LoginLeftView from '@/components/core/views/login/LoginLeftView.vue'
  
  const router = useRouter()
  const showInputLabel = ref(false)

  const systemName = AppConfig.systemInfo.name
  const contact = ref('')
  const captcha = ref('')
  const newPassword = ref('')
  const confirmPassword = ref('')
  const loading = ref(false)
  const countdown = ref(0)
  let timer: any = null

  const register = async () => {
    if (!contact.value) {
      ElMessage.error('请输入邮箱');
      return;
    }
    if (!captcha.value) {
      ElMessage.error('请输入验证码');
      return;
    }
    if (!newPassword.value) {
      ElMessage.error('请输入新密码');
      return;
    }
    if (!confirmPassword.value) {
      ElMessage.error('请确认新密码');
      return;
    }
    if (newPassword.value !== confirmPassword.value) {
      ElMessage.error('两次输入的新密码不一致');
      return;
    }
    loading.value = true;
    try {
      await UserService.resetPassword({
        contact: contact.value,
        captcha: captcha.value,
        new_password: newPassword.value
      });
      ElMessage.success('密码重置成功，请登录');
      setTimeout(() => {
        router.push('/login');
      }, 1000);
    } catch (err) {
      ElMessage.error('重置失败，请检查输入信息或网络');
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  const toLogin = () => {
    router.push('/login')
  }

  const sendCaptcha = async () => {
    if (!contact.value) {
      ElMessage.error('请先输入邮箱');
      return;
    }
    try {
      await api.post({ url: '/api/send-captcha', data: { contact: contact.value } });
      ElMessage.success('验证码已发送，请查收邮箱');
      countdown.value = 60;
      timer = setInterval(() => {
        countdown.value--;
        if (countdown.value <= 0) {
          clearInterval(timer);
        }
      }, 1000);
    } catch (err) {
      ElMessage.error('验证码发送失败');
    }
  }

  defineExpose({
    countdown,
    sendCaptcha
  })
</script>

<style lang="scss" scoped>
  @use '../login/index';
</style>
