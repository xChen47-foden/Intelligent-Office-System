<template>
  <div class="contacts-page">
    <el-button type="primary" @click="showAdd = true">添加联系人</el-button>
    <el-table :data="contacts" style="margin-top: 20px">
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="phone" label="手机号" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="department" label="部门" />
      <el-table-column prop="remark" label="备注" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="danger" size="small" @click="deleteContact(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showAdd" title="添加联系人">
      <el-form :model="form">
        <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="addContact">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/http'
import { ElMessage } from 'element-plus'
type Contact = {
  id: string;
  name: string;
  phone: string;
  email: string;
  department: string;
  remark: string;
}
const contacts = ref<Contact[]>([])
const showAdd = ref(false)
const form = ref({ name: '', phone: '', email: '', department: '', remark: '' })
function loadContacts() {
  api.get<{ code: number; data: any[] }>({ url: '/api/contact/list' }).then((res) => {
    if (res.code === 0) contacts.value = res.data
  })
}
function addContact() {
  api.post<{ code: number; msg?: string }>({ url: '/api/contact/add', data: form.value }).then((res) => {
    if (res.code === 0) {
      ElMessage.success('好友申请已发送')
      showAdd.value = false
      form.value = { name: '', phone: '', email: '', department: '', remark: '' }
      loadContacts()
    }
  })
}
function deleteContact(id: string) {
  api.post<{ code: number; msg?: string }>({ url: '/api/contact/delete', data: { id } }).then((res) => {
    if (res.code === 0) {
      ElMessage.success('删除成功')
      loadContacts()
    }
  })
}
onMounted(loadContacts)
</script>
<style scoped>
.contacts-page {
  padding: 24px;
}
</style> 