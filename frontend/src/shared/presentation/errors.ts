import { isApiError } from '@/shared/api/client'

export function errorMessage(error: unknown): string {
  if (isApiError(error)) {
    if (error.status === 0) return error.message
    if (error.status === 404)
      return 'Нужные данные не найдены. Обновите страницу и попробуйте ещё раз.'
    if (error.status === 422) return 'Проверьте заполненные данные и попробуйте ещё раз.'
    return 'Не удалось выполнить действие. Попробуйте ещё раз.'
  }
  return error instanceof Error ? error.message : 'Произошла неизвестная ошибка.'
}
