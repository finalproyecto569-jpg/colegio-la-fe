const inputBuscar = document.getElementById("buscar");
const selectRol = document.getElementById("filtroRol");
const cuerpoTabla = document.getElementById("cuerpoTabla");
const totalResultados = document.getElementById("totalResultados");
let temporizador = null;

document.getElementById("formFiltros").addEventListener("submit", function (e) {
    e.preventDefault();
    buscarUsuarios();
});

inputBuscar.addEventListener("input", function () {
    clearTimeout(temporizador);
    temporizador = setTimeout(buscarUsuarios, 300);
});

selectRol.addEventListener("change", buscarUsuarios);

async function buscarUsuarios() {
    const parametros = new URLSearchParams({ q: inputBuscar.value, rol: selectRol.value });

    history.replaceState(null, "", "?" + parametros.toString());

    try {
        const respuesta = await fetch("/usuarios/api?" + parametros.toString());
        const usuarios = await respuesta.json();
        dibujarTabla(usuarios);
    } catch (error) {
        console.error("Error al buscar:", error);
    }
}

function dibujarTabla(usuarios) {
    totalResultados.textContent = usuarios.length;

    if (usuarios.length === 0) {
        cuerpoTabla.innerHTML = '<tr><td colspan="7" class="vacio">No se encontraron usuarios.</td></tr>';
        return;
    }

    let html = "";
    usuarios.forEach(function (u) {
        html += "<tr>" +
            "<td><strong>" + escapar(u.nombre) + "</strong></td>" +
            "<td>" + escapar(u.documento) + "</td>" +
            "<td>" + escapar(u.correo) + "</td>" +
            '<td><span class="etiqueta-rol rol-' + u.rol + '">' + mayuscula(u.rol) + "</span></td>" +
            "<td>" + (escapar(u.programa) || "—") + "</td>" +
            "<td>" + (u.activo ? '<span class="etiqueta nivel-baja">Activo</span>'
                               : '<span class="etiqueta estado-cerrada">Inactivo</span>') + "</td>" +
            '<td><div class="acciones">' +
                '<a href="/usuarios/' + u.id + '/editar" class="btn btn-claro btn-sm">Editar</a>' +
                '<form method="post" action="/usuarios/' + u.id + '/eliminar" data-confirmar="Se eliminará a ' +
                    escapar(u.nombre) + ' y toda su información relacionada.">' +
                    '<button class="btn btn-claro btn-sm" title="Eliminar">Eliminar</button></form>' +
            "</div></td></tr>";
    });

    cuerpoTabla.innerHTML = html;
}

function escapar(texto) {
    const div = document.createElement("div");
    div.textContent = texto || "";
    return div.innerHTML;
}

function mayuscula(texto) {
    return texto.charAt(0).toUpperCase() + texto.slice(1);
}
