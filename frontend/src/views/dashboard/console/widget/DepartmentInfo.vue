<template>
  <div class="department-info art-custom-card">
    <div class="header">
      <div class="icon-circle">
        <i class="el-icon-office-building"></i>
      </div>
      <h3 class="title">部门信息</h3>
    </div>
    
    <div class="content">
      <div class="section">
        <div class="section-label">当前部门：</div>
        <div class="department-name">{{ departmentData.name }}</div>
      </div>
      
      <div class="section">
        <div class="section-title">部门职责</div>
        <div class="responsibility-list">
          <div 
            v-for="(item, index) in departmentData.responsibilities" 
            :key="index" 
            class="responsibility-item"
          >
            {{ item }}
          </div>
        </div>
      </div>
      
      <div class="section">
        <div class="section-title">部门成员</div>
        <div class="member-info">
          <div class="member-item" v-if="departmentData.leader">
            <span class="member-role">部长：</span>
            <span class="member-name">{{ departmentData.leader }}</span>
          </div>
          <div class="member-item" v-if="departmentData.members && departmentData.members.length > 0">
            <span class="member-role">专员：</span>
            <span class="member-name">{{ departmentData.members.join('、') }}</span>
          </div>
        </div>
      </div>
      
      <div class="section">
        <div class="section-title">联系方式</div>
        <div class="contact-info">
          <div class="contact-item">
            <span class="contact-label">邮箱：</span>
            <span class="contact-value">{{ departmentData.email }}</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">电话：</span>
            <span class="contact-value">{{ departmentData.phone }}</span>
          </div>
        </div>
      </div>
      
      <div class="section" v-if="departmentData.announcement">
        <div class="section-title">部门公告</div>
        <div class="announcement">
          <i class="el-icon-info"></i>
          <span>{{ departmentData.announcement }}</span>
          <i class="el-icon-close close-btn"></i>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DepartmentData {
  name: string
  responsibilities: string[]
  leader: string
  members: string[]
  email: string
  phone: string
  announcement?: string
}

const props = defineProps<{
  data?: DepartmentData
}>()

const departmentData = computed(() => {
  return props.data || {
    name: '人事部',
    responsibilities: [
      '负责公司招聘、员工入职与离职管理',
      '组织员工培训与绩效考核',
      '管理员工档案与薪酬福利',
      '推动企业文化建设与员工关系维护'
    ],
    leader: '张三',
    members: ['李四', '王五'],
    email: 'hr@company.com',
    phone: '010-12345678',
    announcement: '本月员工生日会将于25日举行，请大家准时参加！'
  }
})
</script>

<style lang="scss" scoped>
.department-info {
  padding: 24px;
  background: var(--art-main-bg-color);
  border-radius: calc(var(--custom-radius) + 4px);
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
  
  .header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    
    .icon-circle {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;
      
      i {
        font-size: 18px;
        color: white;
      }
    }
    
    .title {
      font-size: 18px;
      font-weight: 600;
      color: var(--art-gray-900);
      margin: 0;
    }
  }
  
  .content {
    .section {
      margin-bottom: 20px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .section-label {
        display: inline-block;
        font-size: 14px;
        color: var(--art-gray-600);
        margin-right: 8px;
      }
      
      .department-name {
        display: inline-block;
        font-size: 16px;
        font-weight: 600;
        color: #667eea;
      }
      
      .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 12px;
        padding-left: 8px;
        border-left: 3px solid #667eea;
      }
      
      .responsibility-list {
        .responsibility-item {
          padding: 8px 0;
          padding-left: 20px;
          color: var(--art-gray-700);
          font-size: 14px;
          position: relative;
          
          &:before {
            content: '';
            position: absolute;
            left: 8px;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 4px;
            background: #a8b8f0;
            border-radius: 50%;
          }
        }
      }
      
      .member-info {
        .member-item {
          margin-bottom: 8px;
          color: var(--art-gray-700);
          font-size: 14px;
          
          .member-role {
            color: #f39c12;
            font-weight: 600;
          }
          
          .member-name {
            color: var(--art-gray-800);
          }
        }
      }
      
      .contact-info {
        .contact-item {
          margin-bottom: 8px;
          color: var(--art-gray-700);
          font-size: 14px;
          
          .contact-label {
            color: var(--art-gray-600);
            min-width: 60px;
            display: inline-block;
          }
          
          .contact-value {
            color: var(--art-gray-700);
            background: var(--el-color-primary-light-9);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
          }
        }
      }
      
      .announcement {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--art-gray-700);
        font-size: 14px;
        position: relative;
        
        i.el-icon-info {
          color: #3b82f6;
          font-size: 16px;
        }
        
        .close-btn {
          position: absolute;
          right: 12px;
          color: var(--art-gray-400);
          cursor: pointer;
          
          &:hover {
            color: var(--art-gray-600);
          }
        }
      }
    }
  }
}

.dark {
  .department-info {
    .announcement {
      background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
      border-left-color: #60a5fa;
      
      i.el-icon-info {
        color: #60a5fa;
      }
    }
  }
}
</style> 