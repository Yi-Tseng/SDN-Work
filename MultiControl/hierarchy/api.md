API define

Global to local
----
- Ask host(cmd = 'ask_host')

``
{
    "cmd": "ask_host",
    host: { ip:"10.0.0.1", mac:"00:00:00:00:00:01"},
}
``

- Route result

`
{
	cmd: "route_result",
	port: {dpid: 1, port: 1}
}
`


Local to global
----
- Response host(cmd = 'reponse_host')

`
{
    cmd: "response_host",
    host: { ip:"10.0.0.1", mac:"00:00:00:00:00:01"}
}
`

- Get route

`
{
    cmd: "get_route",
    src:"domain 1", // local controller 1 domain
    dst:{ ip:"10.0.0.3", mac:"00:00:00:00:00:03"}
}
`
- Add cross domain link

`
{
	cmd: "add_cross_domain_link",
	src: {dpid: 4, port: 3},
	dst: {dpid: 1, port: 1}
}
`
