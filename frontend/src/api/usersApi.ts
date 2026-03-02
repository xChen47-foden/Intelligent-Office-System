// 用户相关API接口 - 提供用户登录、信息获取、更新等功能
import request from '@/utils/http'
import { BaseResult } from '@/types/axios'

// 登录参数接口
interface LoginParams {
  username: string
  password: string
  department: string
}

// 用户服务类
export class UserService {
  // 登录
  static login(params: LoginParams) {
    return request.post<BaseResult>({
      url: '/auth/login',
      data: params
    })
  }

  // 获取用户信息
  static getUserInfo() {
    return request.get<BaseResult>({
      url: '/auth/getUserInfo'
    })
  }

  // 新增：更新用户信息
  static updateUserInfo(data: { realName: string; nickName: string }) {
    return request.post<BaseResult>({
      url: '/auth/updateUserInfo',
      data
    })
  }

  // 新增：保存用户偏好设置
  static updatePreferences(data: { theme: string; language: string }) {
    return request.post<BaseResult>({
      url: '/auth/updatePreferences',
      data
    })
  }

  // 新增：上传头像
  static uploadAvatar(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return request.post<BaseResult>({
      url: '/api/user/upload-avatar',
      data: formData
    })
  }

  // 新增：重置密码（忘记密码）
  static resetPassword(data: { contact: string; captcha: string; new_password: string }) {
    return request.post<BaseResult>({
      url: '/api/reset-password',
      data
    })
  }

  // 新增：生成随机头像
  static generateAvatar() {
    return request.post<BaseResult>({
      url: '/api/user/generate-avatar'
    })
  }
}
