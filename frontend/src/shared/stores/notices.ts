import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNoticesStore = defineStore('notices', () => {
  const actionMessage = ref('')
  function setMessage(message: string) {
    actionMessage.value = message
  }
  function clearActionMessage() {
    actionMessage.value = ''
  }
  return { actionMessage, setMessage, clearActionMessage }
})
