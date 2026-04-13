import axios from 'axios'
import { GW, currentUser, authHeaders } from './useAuth'

const MEDIA_GW = GW

// Загрузить файл в Media-service, вернуть uuid
async function uploadFile(file, uploadContext = 'chat_message_files') {
  const form = new FormData()
  form.append('file', file)

  const { data } = await axios.post(
    `${MEDIA_GW}/media_service/upload`,
    form,
    {
      headers: { ...authHeaders() },
      params: {
        upload_context: uploadContext,
        entity_id: currentUser.value?.user_id ?? 0,
      },
    }
  )
  return data.file.uuid
}

// Получить метаданные файла (s3_url, content_type, category)
async function getFileMeta(uuid) {
  const { data } = await axios.get(`${MEDIA_GW}/media_service/files/${uuid}/`)
  return data
}

// Привязать файл к сообщению
async function linkFile(uuid) {
  await axios.patch(`${MEDIA_GW}/media_service/files/${uuid}/link/`, {}, {
    headers: authHeaders(),
  })
}

// Загрузить несколько файлов, вернуть { uuids, failed } — успешные и неудачные
async function uploadFiles(files, uploadContext = 'chat_message_files') {
  const results = await Promise.allSettled(
    files.map(file => uploadFile(file, uploadContext))
  )
  const uuids = []
  let failed = 0
  results.forEach(r => {
    if (r.status === 'fulfilled') uuids.push(r.value)
    else failed++
  })
  return { uuids, failed }
}

// Получить s3_url для списка uuid
async function resolveFileUrls(uuids) {
  const results = await Promise.all(uuids.map(uuid => getFileMeta(uuid).catch(() => null)))
  return results.filter(Boolean)
}

export { uploadFile, uploadFiles, getFileMeta, linkFile, resolveFileUrls }
