let _cachedKey = null

async function getPublicKey() {
  if (_cachedKey) return _cachedKey
  const res = await fetch('/api/auth/public-key')
  const { public_key } = await res.json()
  const keyData = Uint8Array.from(atob(public_key), c => c.charCodeAt(0))
  _cachedKey = await crypto.subtle.importKey(
    'spki', keyData, { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['encrypt']
  )
  return _cachedKey
}

export async function encryptPassword(password) {
  const key = await getPublicKey()
  const encrypted = await crypto.subtle.encrypt(
    { name: 'RSA-OAEP' }, key, new TextEncoder().encode(password)
  )
  return btoa(String.fromCharCode(...new Uint8Array(encrypted)))
}
