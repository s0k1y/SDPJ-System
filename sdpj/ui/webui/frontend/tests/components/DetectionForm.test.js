import { describe, it, expect } from 'vitest'

// 测试多模态节点 ID 映射逻辑
describe('Multimodal ID mapping', () => {
  const MULTIMODAL_CHILDREN = [
    { id: 'multi-modal:jpg', label: 'JPG 图像', contentType: 'image_url' },
    { id: 'multi-modal:png', label: 'PNG 图像', contentType: 'image_url' },
    { id: 'multi-modal:mp3', label: 'MP3 音频', contentType: 'input_audio' },
    { id: 'multi-modal:wav', label: 'WAV 音频', contentType: 'input_audio' },
  ]

  const _MULTIMODAL_IDS = new Set(MULTIMODAL_CHILDREN.map(c => c.id))
  const _CONTENT_TYPE_MAP = Object.fromEntries(MULTIMODAL_CHILDREN.map(c => [c.id, c.contentType]))

  it('should identify multimodal IDs correctly', () => {
    expect(_MULTIMODAL_IDS.has('multi-modal:jpg')).toBe(true)
    expect(_MULTIMODAL_IDS.has('multi-modal:png')).toBe(true)
    expect(_MULTIMODAL_IDS.has('multi-modal:mp3')).toBe(true)
    expect(_MULTIMODAL_IDS.has('multi-modal:wav')).toBe(true)
    expect(_MULTIMODAL_IDS.has('direct')).toBe(false)
    expect(_MULTIMODAL_IDS.has('base64')).toBe(false)
  })

  it('should map multimodal IDs to content types', () => {
    expect(_CONTENT_TYPE_MAP['multi-modal:jpg']).toBe('image_url')
    expect(_CONTENT_TYPE_MAP['multi-modal:png']).toBe('image_url')
    expect(_CONTENT_TYPE_MAP['multi-modal:mp3']).toBe('input_audio')
    expect(_CONTENT_TYPE_MAP['multi-modal:wav']).toBe('input_audio')
  })

  it('should extract modalities from multimodal paths', () => {
    const paths = ['direct', 'multi-modal:jpg', 'multi-modal:mp3', 'base64']
    const modalities = paths
      .filter(p => p.startsWith('multi-modal:'))
      .map(p => p.split(':')[1])
    expect(modalities).toEqual(['jpg', 'mp3'])
  })

  it('should filter effective attack paths correctly', () => {
    const encodingLeafIds = new Set(['base64', 'rot13'])
    const paths = ['direct', 'multi-modal:jpg', 'multi-modal:mp3', 'base64', 'multi_encoding']
    const effective = paths.filter(id =>
      id === 'direct' || _MULTIMODAL_IDS.has(id) || encodingLeafIds.has(id)
    )
    expect(effective).toEqual(['direct', 'multi-modal:jpg', 'multi-modal:mp3', 'base64'])
  })
})

// 测试多模态警告逻辑
describe('Multimodal warning logic', () => {
  const MULTIMODAL_CHILDREN = [
    { id: 'multi-modal:jpg', contentType: 'image_url' },
    { id: 'multi-modal:png', contentType: 'image_url' },
    { id: 'multi-modal:mp3', contentType: 'input_audio' },
    { id: 'multi-modal:wav', contentType: 'input_audio' },
  ]

  const _CONTENT_TYPE_MAP = Object.fromEntries(MULTIMODAL_CHILDREN.map(c => [c.id, c.contentType]))

  it('should detect unsupported modalities', () => {
    const selectedPaths = ['multi-modal:jpg', 'multi-modal:mp3']
    const supportedTypes = ['image_url'] // only image_url supported

    const unsupported = selectedPaths.filter(id => {
      const ct = _CONTENT_TYPE_MAP[id]
      return ct && !supportedTypes.includes(ct)
    })
    expect(unsupported).toEqual(['multi-modal:mp3'])
  })

  it('should pass when all modalities are supported', () => {
    const selectedPaths = ['multi-modal:jpg', 'multi-modal:mp3']
    const supportedTypes = ['image_url', 'input_audio']

    const unsupported = selectedPaths.filter(id => {
      const ct = _CONTENT_TYPE_MAP[id]
      return ct && !supportedTypes.includes(ct)
    })
    expect(unsupported).toEqual([])
  })

  it('should handle non-openai adapter', () => {
    const isOpenAi = false
    const selectedPaths = ['multi-modal:jpg']

    const hasUnsupported = isOpenAi ? selectedPaths.some(id => {
      const ct = _CONTENT_TYPE_MAP[id]
      return ct && !['image_url', 'input_audio'].includes(ct)
    }) : selectedPaths.length > 0

    expect(hasUnsupported).toBe(true)
  })
})
