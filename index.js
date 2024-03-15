import fetch from 'node-fetch'
import pkg from 'request-promise';
const { get, put, post } = pkg;

const indicators = {}
const dimensions = {}

function authUrl(rbd) {
    const queryParams = 'auth?client_id=agencia&response_type=code&state=1&scope=docente'
    const redirect = `redirect_uri=https://www.simce.cl/validation/${rbd}`
    const baseUrl = 'https://perfilador.agenciaeducacion.cl/auth/realms/Perfilador/protocol/openid-connect/'
    return `${baseUrl}${queryParams}&${redirect}`
}

async function getCookie(){
    const res = await fetch(authUrl(8888))
    return res.headers.get('set-cookie')
}

async function main() {
    try {
        const options = {
            uri: 'https://www.simce.cl/8888/indicador',
            cookie: getCookie()
        }
        const res = await get(options)
        console.log(res)
    } catch (e) {
        console.log(e)
    }
}
main()