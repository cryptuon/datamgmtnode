<template>
  <div class="overflow-x-auto">
    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key" :class="column.class">
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-if="loading">
          <td :colspan="columns.length" class="text-center py-8 text-gray-500">
            Loading...
          </td>
        </tr>
        <tr v-else-if="!data || data.length === 0">
          <td :colspan="columns.length" class="text-center py-8 text-gray-500">
            {{ emptyMessage }}
          </td>
        </tr>
        <tr v-else v-for="(row, index) in data" :key="index">
          <td v-for="column in columns" :key="column.key" :class="column.cellClass">
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
              {{ formatValue(row[column.key], column) }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  columns: {
    type: Array,
    required: true
    // [{ key: 'id', label: 'ID', class: '', cellClass: '', format: (v) => v }]
  },
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  emptyMessage: {
    type: String,
    default: 'No data available'
  }
})

const formatValue = (value, column) => {
  if (column.format && typeof column.format === 'function') {
    return column.format(value)
  }
  if (value === null || value === undefined) {
    return '-'
  }
  return value
}
</script>
