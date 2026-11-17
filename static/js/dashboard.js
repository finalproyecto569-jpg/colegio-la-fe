document.addEventListener("DOMContentLoaded", cargarDatos);

async function cargarDatos() {
    try {
        const respuesta = await fetch("/api/dashboard");
        if (!respuesta.ok) throw new Error("Error " + respuesta.status);
        const datos = await respuesta.json();
        dibujarBarras("graficaPromedios", datos.grupos, "promedio", 5, 3.0, "");
    } catch (error) {
        console.error(error);
        document.getElementById("graficaPromedios").innerHTML = '<p class="suave">No se pudieron cargar los datos.</p>';
    }
}

function dibujarBarras(idContenedor, lista, campo, maximo, limite, sufijo) {
    const contenedor = document.getElementById(idContenedor);
    contenedor.innerHTML = "";

    if (lista.length === 0) {
        contenedor.innerHTML = '<p class="suave">Sin datos todavía.</p>';
        return;
    }

    lista.forEach(function (item) {
        const valor = item[campo];
        const fila = document.createElement("div");
        fila.className = "barra-fila";
        fila.title = item.nombre;
        fila.innerHTML =
            "<span>" + item.curso + "</span>" +
            '<div class="barra-fondo"><div class="barra-relleno"></div></div>' +
            "<strong>" + valor + sufijo + "</strong>";
        contenedor.appendChild(fila);

        const relleno = fila.querySelector(".barra-relleno");
        if (valor < limite) relleno.classList.add("baja");

        setTimeout(function () {
            relleno.style.width = (valor / maximo * 100) + "%";
        }, 100);
    });
}
