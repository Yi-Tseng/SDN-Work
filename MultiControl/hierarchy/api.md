API define

Global to local
----
- Set agent id

``
{
    cmd: "set_agent_id",
    agent_id: 1
}


- Ask host(cmd = 'ask_host')

``
{
    "cmd": "ask_host",
    host: "00:00:00:00:00:01",
}
``

- Ask dpid

``
{
    cmd: 'ask_dpid',
    dpid: 1
}
``

- Route result

``
{
	cmd: "route_result",
	dpid: 1,
    port: 1,
    host: '00:00:00:00:00:01'
}
``

P.S. if dpid = -1, global route query failed


Local to global
----
- Response host(cmd = 'reponse_host')

``
{
    cmd: "response_host",
    host: "00:00:00:00:00:01"
}
``

- Get route

``
{
    cmd: "get_route",
    dst:"00:00:00:00:00:03"
}
``
- Add cross domain link

``
{
	cmd: "add_cross_domain_link",
	src: {dpid: 4, port: 3}, # this should from local controller
	dst: {dpid: 1, port: 1}
}
``

- Response dpid

``
{
    cmd: 'response_dpid',
    dpid: 1,
}
``




