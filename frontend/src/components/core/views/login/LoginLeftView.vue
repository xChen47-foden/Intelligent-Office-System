<template>
  <div class="left-view">
    <div class="logo">
      <svg class="icon" aria-hidden="true">
        <use xlink:href="#iconsys-zhaopian-copy"></use>
      </svg>
      <h1 class="title">{{ AppConfig.systemInfo.name }}</h1>
    </div>
    
    <!-- 背景图片区域 -->
    <div class="left-bg"></div>
    
    <!-- 图标图片区域 -->
    <div class="left-img"></div>

    <div class="text-wrap">
      <h1> {{ $t('login.leftView.title') }} </h1>
      <p> {{ $t('login.leftView.subTitle') }} </p>
    </div>
  </div>
</template>

<script setup lang="ts">
  import AppConfig from '@/config'
  
  // 直接使用相对路径
  const bgImage = '/img/login/lf_bg.png'
  const iconImage = '/img/login/lf_icon2.png'
  
  // 设置CSS变量
  const setCssVariables = () => {
    document.documentElement.style.setProperty('--bg-image', `url(${bgImage})`)
    document.documentElement.style.setProperty('--icon-image', `url(${iconImage})`)
  }
  
  // 组件挂载时设置CSS变量
  import { onMounted } from 'vue'
  onMounted(() => {
    setCssVariables()
  })
</script>

<style lang="scss" scoped>
  .left-view {
    position: relative;
    width: 100%;
    height: 100%;
    
    .left-bg {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-image: url('/img/login/lf_bg.png');
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      z-index: 1;
    }
    
    .left-img {
      position: relative;
      z-index: 10;
      display: block;
      width: 560px;
      height: 400px;
      margin: auto;
      margin-top: 15vh;
      background-image: url('/img/login/lf_icon2.png');
      background-size: contain;
      background-position: center;
      background-repeat: no-repeat;
    }
  }
</style>
