<template>
  <div class="avatar-picker">
    <div class="avatar-display">
      <el-avatar :size="size" :src="displayAvatar" @error="onAvatarError" />
    </div>
    
    <div class="avatar-actions">
      <el-button-group>
        <el-button type="primary" size="small" @click="showPicker = true">
          选择头像
        </el-button>
        <el-button type="success" size="small" @click="generateRandomAvatar">
          随机头像
        </el-button>
        <el-button type="info" size="small" @click="triggerUpload">
          上传头像
        </el-button>
      </el-button-group>
    </div>

    <!-- 头像选择器对话框 -->
    <el-dialog
      v-model="showPicker"
      title="选择头像"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="avatar-picker-content">
        <el-tabs v-model="activeTab" @tab-click="handleTabClick">
          <el-tab-pane label="本地头像" name="local">
            <div class="avatar-grid">
              <div
                v-for="avatar in localAvatars"
                :key="avatar.id"
                class="avatar-item"
                :class="{ active: selectedAvatar === avatar.url }"
                @click="selectAvatar(avatar.url)"
              >
                <el-avatar :size="60" :src="avatar.url" />
                <span class="avatar-name">{{ avatar.name }}</span>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="在线头像" name="online">
            <div class="online-avatars">
              <el-row :gutter="10">
                <el-col :span="8" v-for="(avatar, index) in onlineAvatars" :key="index">
                  <div
                    class="avatar-item"
                    :class="{ active: selectedAvatar === avatar }"
                    @click="selectAvatar(avatar)"
                  >
                    <el-avatar :size="60" :src="avatar" />
                  </div>
                </el-col>
              </el-row>
              <div class="generate-more" style="margin-top: 20px;">
                <el-button type="primary" @click="generateMoreOnlineAvatars">
                  生成更多头像
                </el-button>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPicker = false">取消</el-button>
          <el-button type="primary" @click="confirmSelection">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 隐藏的文件上传input -->
    <input
      ref="uploadInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleFileUpload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  localAvatars, 
  generateRandomAvatar, 
  getRandomPresetAvatar,
  presetAvatars
} from '@/utils/avatars'

// Props
interface Props {
  modelValue?: string
  size?: number
  uploadUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  size: 80,
  uploadUrl: '/api/user/upload-avatar'
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string]
  'upload-success': [result: any]
}>()

// 响应式数据
const showPicker = ref(false)
const activeTab = ref('local')
const selectedAvatar = ref('')
const onlineAvatars = ref<string[]>([])
const uploadInput = ref<HTMLInputElement>()

// 计算属性
const displayAvatar = computed(() => {
  return props.modelValue || '/src/assets/img/avatar/avatar.png'
})

// 初始化在线头像
const initOnlineAvatars = () => {
  onlineAvatars.value = presetAvatars.slice(0, 9)
}

// 生成更多在线头像
const generateMoreOnlineAvatars = () => {
  const newAvatars = []
  for (let i = 0; i < 9; i++) {
    newAvatars.push(generateRandomAvatar())
  }
  onlineAvatars.value = newAvatars
}

// 选择头像
const selectAvatar = (url: string) => {
  selectedAvatar.value = url
}

// 确认选择
const confirmSelection = () => {
  if (selectedAvatar.value) {
    emit('update:modelValue', selectedAvatar.value)
    emit('change', selectedAvatar.value)
    showPicker.value = false
    ElMessage.success('头像选择成功')
  }
}

// 生成随机头像
const generateRandomAvatar = () => {
  const randomAvatar = getRandomPresetAvatar()
  emit('update:modelValue', randomAvatar)
  emit('change', randomAvatar)
  ElMessage.success('随机头像生成成功')
}

// 触发上传
const triggerUpload = () => {
  uploadInput.value?.click()
}

// 处理文件上传
const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  
  // 验证文件大小（限制为5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }
  
  try {
    // 这里可以上传到服务器，或者转换为base64
    const reader = new FileReader()
    reader.onload = (e) => {
      const result = e.target?.result as string
      emit('update:modelValue', result)
      emit('change', result)
      emit('upload-success', { url: result })
      ElMessage.success('头像上传成功')
    }
    reader.readAsDataURL(file)
  } catch (error) {
    ElMessage.error('头像上传失败')
  }
  
  // 清空input
  target.value = ''
}

// 头像加载错误处理
const onAvatarError = (e: Event) => {
  const target = e.target as HTMLImageElement
  target.src = '/src/assets/img/avatar/avatar.png'
}

// 处理标签页点击
const handleTabClick = (tab: any) => {
  if (tab.name === 'online' && onlineAvatars.value.length === 0) {
    initOnlineAvatars()
  }
}

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      selectedAvatar.value = newVal
    }
  },
  { immediate: true }
)

// 初始化
initOnlineAvatars()
</script>

<style scoped>
.avatar-picker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.avatar-display {
  position: relative;
}

.avatar-actions {
  display: flex;
  gap: 8px;
}

.avatar-picker-content {
  max-height: 400px;
  overflow-y: auto;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 16px;
  padding: 16px;
}

.avatar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.avatar-item:hover {
  border-color: var(--el-color-primary-light-7);
  background-color: var(--el-color-primary-light-9);
}

.avatar-item.active {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.avatar-name {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.online-avatars {
  padding: 16px;
}

.online-avatars .avatar-item {
  width: 100%;
  padding: 8px;
  margin-bottom: 8px;
}

.generate-more {
  text-align: center;
  padding: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .avatar-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 12px;
    padding: 12px;
  }
  
  .avatar-item {
    padding: 8px;
  }
}

/* 深色模式适配 */
.dark .avatar-item {
  border-color: var(--el-border-color);
}

.dark .avatar-item:hover {
  border-color: var(--el-color-primary-light-3);
  background-color: var(--el-color-primary-light-8);
}

.dark .avatar-item.active {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-8);
}
</style> 