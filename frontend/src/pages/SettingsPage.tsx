import { useState } from 'react'
import { Key, Server, Save, CheckCircle2 } from 'lucide-react'
import { getApiKey, setApiKey } from '../api/client'

export default function SettingsPage() {
  const [apiKey, setApiKeyInput] = useState(getApiKey())
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setApiKey(apiKey.trim())
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <Server className="w-7 h-7 text-primary-600" />
        设置
      </h1>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
            <Key className="w-4 h-4" />
            API Key
          </label>
          <p className="text-xs text-gray-500 mb-2">
            用于访问后端 API，请与后端管理员确认当前 Key
          </p>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKeyInput(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          />
        </div>

        <button
          onClick={handleSave}
          className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-medium px-5 py-2 rounded-lg transition-colors"
        >
          {saved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saved ? '已保存' : '保存设置'}
        </button>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-medium mb-1">使用提示</p>
        <ul className="list-disc list-inside space-y-1 text-blue-700">
          <li>API Key 保存在浏览器本地，不会上传到服务器</li>
          <li>如需修改后端配置，请联系管理员编辑 .env 文件</li>
          <li>本地 Whisper 模式下，首次使用会自动下载模型文件</li>
          <li>模型越大准确度越高，但处理速度越慢</li>
        </ul>
      </div>
    </div>
  )
}
