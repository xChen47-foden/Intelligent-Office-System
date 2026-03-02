<template>
  <div class="personnel-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h3>👥 人员管理</h3>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            新增人员
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索姓名、用户名、联系方式..."
          clearable
          style="width: 300px; margin-right: 10px;"
          @keyup.enter="loadPersonnelList"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filterDepartment"
          placeholder="选择部门"
          clearable
          style="width: 200px; margin-right: 10px;"
          @change="loadPersonnelList"
        >
          <el-option label="全部部门" value="" />
          <el-option label="人事部" value="人事部" />
          <el-option label="技术部" value="技术部" />
          <el-option label="财务部" value="财务部" />
          <el-option label="市场部" value="市场部" />
          <el-option label="销售部" value="销售部" />
        </el-select>
        <el-button type="primary" @click="loadPersonnelList">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="resetSearch">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>

      <!-- 表格 -->
      <el-table
        :data="personnelList"
        v-loading="loading"
        style="width: 100%; margin-top: 20px;"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="头像" width="80">
          <template #default="{ row }">
            <el-avatar :src="getAvatarUrl(row.avatar)" :size="40">
              {{ row.realName?.[0] || row.username?.[0] || 'U' }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="realName" label="姓名" width="120" />
        <el-table-column prop="nickName" label="昵称" width="120" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column prop="contact" label="联系方式" width="150" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container" style="margin-top: 20px;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadPersonnelList"
          @current-change="loadPersonnelList"
        />
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增人员' : '编辑人员'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" :prop="dialogType === 'add' ? 'password' : ''">
          <el-input
            v-model="formData.password"
            type="password"
            :placeholder="dialogType === 'add' ? '请输入密码' : '留空则不修改密码'"
            show-password
          />
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="formData.realName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickName">
          <el-input v-model="formData.nickName" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="联系方式" prop="contact">
          <el-input v-model="formData.contact" placeholder="请输入手机号或邮箱" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-select v-model="formData.department" placeholder="请选择部门" style="width: 100%;">
            <el-option label="人事部" value="人事部" />
            <el-option label="技术部" value="技术部" />
            <el-option label="财务部" value="财务部" />
            <el-option label="市场部" value="市场部" />
            <el-option label="销售部" value="销售部" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题" prop="theme">
          <el-select v-model="formData.theme" style="width: 100%;">
            <el-option label="自动" value="auto" />
            <el-option label="浅色" value="light" />
            <el-option label="深色" value="dark" />
          </el-select>
        </el-form-item>
        <el-form-item label="语言" prop="language">
          <el-select v-model="formData.language" style="width: 100%;">
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import defaultAvatar from '@/assets/img/avatar/avatar5.jpg'

// 数据
const loading = ref(false)
const personnelList = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const filterDepartment = ref('')

// 对话框
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const submitting = ref(false)
const formRef = ref()

// 表单数据
const formData = ref({
  id: null as number | null,
  username: '',
  password: '',
  realName: '',
  nickName: '',
  contact: '',
  department: '',
  avatar: '',
  theme: 'auto',
  language: 'zh'
})

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  contact: [
    { required: true, message: '请输入联系方式', trigger: 'blur' }
  ],
  department: [
    { required: true, message: '请选择部门', trigger: 'change' }
  ]
}

// 获取头像URL
const getAvatarUrl = (avatar: string) => {
  if (!avatar) return defaultAvatar
  if (avatar.startsWith('http')) return avatar
  if (avatar.startsWith('/uploads/')) return avatar
  return `/uploads/${avatar}`
}

// 加载人员列表
const loadPersonnelList = async () => {
  try {
    loading.value = true
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/personnel/list', {
      params: {
        page: currentPage.value,
        pageSize: pageSize.value,
        department: filterDepartment.value || undefined,
        keyword: searchKeyword.value || undefined
      },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      personnelList.value = res.data.data.list || []
      total.value = res.data.data.total || 0
    } else {
      ElMessage.error(res.data.msg || '获取人员列表失败')
    }
  } catch (error: any) {
    console.error('加载人员列表失败:', error)
    ElMessage.error(error.response?.data?.msg || '获取人员列表失败')
  } finally {
    loading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchKeyword.value = ''
  filterDepartment.value = ''
  currentPage.value = 1
  loadPersonnelList()
}

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = 'add'
  formData.value = {
    id: null,
    username: '',
    password: '',
    realName: '',
    nickName: '',
    contact: '',
    department: '',
    avatar: '',
    theme: 'auto',
    language: 'zh'
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (row: any) => {
  dialogType.value = 'edit'
  formData.value = {
    id: row.id,
    username: row.username,
    password: '',
    realName: row.realName || '',
    nickName: row.nickName || '',
    contact: row.contact || '',
    department: row.department || '',
    avatar: row.avatar || '',
    theme: row.theme || 'auto',
    language: row.language || 'zh'
  }
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const token = localStorage.getItem('token')
    const url = dialogType.value === 'add' ? '/api/personnel/create' : '/api/personnel/update'
    const data = { ...formData.value }
    
    // 如果是编辑且密码为空，不传递密码字段
    if (dialogType.value === 'edit' && !data.password) {
      delete data.password
    }
    
    const res = await axios.post(url, data, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      ElMessage.success(dialogType.value === 'add' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      loadPersonnelList()
    } else {
      ElMessage.error(res.data.msg || '操作失败')
    }
  } catch (error: any) {
    if (error.response?.data?.msg) {
      ElMessage.error(error.response.data.msg)
    } else if (error.message !== 'validation failed') {
      ElMessage.error('操作失败')
    }
  } finally {
    submitting.value = false
  }
}

// 删除人员
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.realName || row.username}" 吗？`,
      '确认删除',
      {
        type: 'warning'
      }
    )

    const token = localStorage.getItem('token')
    const res = await axios.post(
      '/api/personnel/delete',
      { id: row.id },
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )

    if (res.data.code === 0) {
      ElMessage.success('删除成功')
      loadPersonnelList()
    } else {
      ElMessage.error(res.data.msg || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.msg || '删除失败')
    }
  }
}

onMounted(() => {
  loadPersonnelList()
})
</script>

<style scoped lang="scss">
.personnel-page {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .search-bar {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
  }
}
</style>

