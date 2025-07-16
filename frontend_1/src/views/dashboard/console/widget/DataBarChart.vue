<template>
  <div ref="chartRef" class="data-bar-chart"></div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const chartData = ref({
  categories: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月'],
  values: [120, 200, 150, 80, 70, 110, 130, 180, 160]
})

const getOption = () => ({
  title: {
    text: '业务数据统计',
    left: 'center',
    top: 10,
    textStyle: {
      fontSize: 16,
      color: '#2b3a55',
      fontWeight: 600
    }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    },
    formatter: (params: any) => {
      const data = params[0]
      return `${data.name}: ${data.value}`
    }
  },
  grid: { left: 40, right: 20, top: 50, bottom: 30 },
  xAxis: {
    type: 'category',
    data: chartData.value.categories,
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e0e6f1' } },
    axisLabel: { color: '#4b5b77', fontSize: 13 }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f0f0' } },
    axisLabel: { color: '#4b5b77', fontSize: 13 }
  },
  series: [
    {
      name: '业务量',
      type: 'bar',
      data: chartData.value.values,
      barWidth: '40%',
      itemStyle: {
        borderRadius: 6,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#6fa1f7' },
          { offset: 1, color: '#3b7ddd' }
        ])
      }
    }
  ]
})

const loadChartData = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/dashboard/chart-data', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.data.code === 0 && response.data.data) {
      const data = response.data.data
      chartData.value = {
        categories: data.map((item: any) => item.month),
        values: data.map((item: any) => item.value)
      }
      // 更新图表数据
      if (chartInstance) {
        chartInstance.setOption(getOption())
      }
    }
  } catch (error) {
    console.error('获取图表数据失败:', error)
  }
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(async () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption(getOption())
    window.addEventListener('resize', resizeChart)
    
    // 加载图表数据
    await loadChartData()
  }
})
</script>

<style scoped>
.data-bar-chart {
  width: 100%;
  height: 220px;
}
</style> 