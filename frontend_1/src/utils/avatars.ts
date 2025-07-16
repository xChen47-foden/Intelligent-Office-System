// 随机头像工具文件
export interface AvatarOption {
  id: string
  name: string
  url: string
  type: 'svg' | 'img' | 'api'
}

// 本地头像资源
export const localAvatars: AvatarOption[] = [
  {
    id: 'avatar1',
    name: '头像1',
    url: '/src/assets/img/avatar/avatar1.jpg',
    type: 'img'
  },
  {
    id: 'avatar2',
    name: '头像2',
    url: '/src/assets/img/avatar/avatar2.jpg',
    type: 'img'
  },
  {
    id: 'avatar3',
    name: '头像3',
    url: '/src/assets/img/avatar/avatar3.jpg',
    type: 'img'
  },
  {
    id: 'avatar4',
    name: '头像4',
    url: '/src/assets/img/avatar/avatar4.jpg',
    type: 'img'
  },
  {
    id: 'avatar5',
    name: '头像5',
    url: '/src/assets/img/avatar/avatar5.jpg',
    type: 'img'
  },
  {
    id: 'avatar6',
    name: '头像6',
    url: '/src/assets/img/avatar/avatar6.jpg',
    type: 'img'
  },
  {
    id: 'avatar7',
    name: '头像7',
    url: '/src/assets/img/avatar/avatar7.jpg',
    type: 'img'
  },
  {
    id: 'avatar8',
    name: '头像8',
    url: '/src/assets/img/avatar/avatar8.jpg',
    type: 'img'
  },
  {
    id: 'avatar9',
    name: '头像9',
    url: '/src/assets/img/avatar/avatar9.jpg',
    type: 'img'
  },
  {
    id: 'avatar10',
    name: '头像10',
    url: '/src/assets/img/avatar/avatar10.jpg',
    type: 'img'
  }
]

// SVG头像样式
export const svgAvatars: AvatarOption[] = [
  {
    id: 'adventurer',
    name: '冒险家',
    url: 'https://api.dicebear.com/7.x/adventurer/svg',
    type: 'api'
  },
  {
    id: 'avataaars',
    name: '卡通头像',
    url: 'https://api.dicebear.com/7.x/avataaars/svg',
    type: 'api'
  },
  {
    id: 'big-ears',
    name: '大耳朵',
    url: 'https://api.dicebear.com/7.x/big-ears/svg',
    type: 'api'
  },
  {
    id: 'big-smile',
    name: '大笑脸',
    url: 'https://api.dicebear.com/7.x/big-smile/svg',
    type: 'api'
  },
  {
    id: 'bottts',
    name: '机器人',
    url: 'https://api.dicebear.com/7.x/bottts/svg',
    type: 'api'
  },
  {
    id: 'croodles',
    name: '涂鸦',
    url: 'https://api.dicebear.com/7.x/croodles/svg',
    type: 'api'
  },
  {
    id: 'fun-emoji',
    name: '有趣表情',
    url: 'https://api.dicebear.com/7.x/fun-emoji/svg',
    type: 'api'
  },
  {
    id: 'icons',
    name: '图标',
    url: 'https://api.dicebear.com/7.x/icons/svg',
    type: 'api'
  },
  {
    id: 'identicon',
    name: '几何图形',
    url: 'https://api.dicebear.com/7.x/identicon/svg',
    type: 'api'
  },
  {
    id: 'lorelei',
    name: '洛蕾莱',
    url: 'https://api.dicebear.com/7.x/lorelei/svg',
    type: 'api'
  },
  {
    id: 'micah',
    name: '米卡',
    url: 'https://api.dicebear.com/7.x/micah/svg',
    type: 'api'
  },
  {
    id: 'miniavs',
    name: '迷你头像',
    url: 'https://api.dicebear.com/7.x/miniavs/svg',
    type: 'api'
  },
  {
    id: 'open-peeps',
    name: '开放人物',
    url: 'https://api.dicebear.com/7.x/open-peeps/svg',
    type: 'api'
  },
  {
    id: 'personas',
    name: '人物',
    url: 'https://api.dicebear.com/7.x/personas/svg',
    type: 'api'
  },
  {
    id: 'pixel-art',
    name: '像素艺术',
    url: 'https://api.dicebear.com/7.x/pixel-art/svg',
    type: 'api'
  },
  {
    id: 'shapes',
    name: '形状',
    url: 'https://api.dicebear.com/7.x/shapes/svg',
    type: 'api'
  },
  {
    id: 'thumbs',
    name: '拇指',
    url: 'https://api.dicebear.com/7.x/thumbs/svg',
    type: 'api'
  }
]

// 生成随机种子
export function generateRandomSeed(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 10; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// 生成随机头像URL
export function generateRandomAvatar(): string {
  const seed = generateRandomSeed()
  const style = svgAvatars[Math.floor(Math.random() * svgAvatars.length)]
  const backgroundColor = [
    'b6e3f4', 'c0aede', 'd1d4f9', 'ffd5dc', 'ffdfbf', 
    'e6f3ff', 'fff2e6', 'f0f9ff', 'fef7f0', 'f7f0ff'
  ]
  const bgColor = backgroundColor[Math.floor(Math.random() * backgroundColor.length)]
  
  return `${style.url}?seed=${seed}&backgroundColor=${bgColor}&size=200`
}

// 获取本地随机头像
export function getRandomLocalAvatar(): string {
  const avatar = localAvatars[Math.floor(Math.random() * localAvatars.length)]
  return avatar.url
}

// 获取所有头像选项
export function getAllAvatars(): AvatarOption[] {
  return [...localAvatars, ...svgAvatars]
}

// 根据类型获取头像
export function getAvatarsByType(type: 'svg' | 'img' | 'api'): AvatarOption[] {
  return getAllAvatars().filter(avatar => avatar.type === type)
}

// 预置的一些精美头像URL（备用）
export const presetAvatars = [
  // 可爱动物系列
  'https://api.dicebear.com/7.x/adventurer/svg?seed=cute1&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/adventurer/svg?seed=cute2&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/adventurer/svg?seed=cute3&backgroundColor=d1d4f9',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=happy1&backgroundColor=ffd5dc',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=happy2&backgroundColor=ffdfbf',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=happy3&backgroundColor=e6f3ff',
  
  // 机器人系列
  'https://api.dicebear.com/7.x/bottts/svg?seed=robot1&backgroundColor=f0f9ff',
  'https://api.dicebear.com/7.x/bottts/svg?seed=robot2&backgroundColor=fef7f0',
  'https://api.dicebear.com/7.x/bottts/svg?seed=robot3&backgroundColor=f7f0ff',
  
  // 几何图形系列
  'https://api.dicebear.com/7.x/identicon/svg?seed=geo1&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/identicon/svg?seed=geo2&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/identicon/svg?seed=geo3&backgroundColor=d1d4f9',
  
  // 像素艺术系列
  'https://api.dicebear.com/7.x/pixel-art/svg?seed=pixel1&backgroundColor=ffd5dc',
  'https://api.dicebear.com/7.x/pixel-art/svg?seed=pixel2&backgroundColor=ffdfbf',
  'https://api.dicebear.com/7.x/pixel-art/svg?seed=pixel3&backgroundColor=e6f3ff',
  
  // 表情系列
  'https://api.dicebear.com/7.x/fun-emoji/svg?seed=emoji1&backgroundColor=f0f9ff',
  'https://api.dicebear.com/7.x/fun-emoji/svg?seed=emoji2&backgroundColor=fef7f0',
  'https://api.dicebear.com/7.x/fun-emoji/svg?seed=emoji3&backgroundColor=f7f0ff',
  
  // 人物系列
  'https://api.dicebear.com/7.x/personas/svg?seed=person1&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/personas/svg?seed=person2&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/personas/svg?seed=person3&backgroundColor=d1d4f9'
]

// 获取随机预置头像
export function getRandomPresetAvatar(): string {
  return presetAvatars[Math.floor(Math.random() * presetAvatars.length)]
} 