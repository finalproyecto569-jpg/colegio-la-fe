const formAsistencia = document.getElementById("formAsistencia");

if (formAsistencia) {

    document.getElementById("fecha").addEventListener("change", function () {
        document.getElementById("formFecha").submit();
    });

    const filas = formAsistencia.querySelectorAll(".opciones-asistencia");

    function contar() {
        const conteo = { presente: 0, ausente: 0, justificada: 0, sin: 0 };
        filas.forEach(function (grupo) {
            const marcado = grupo.querySelector("input:checked");
            if (marcado) conteo[marcado.value]++;
            else conteo.sin++;
        });
        document.getElementById("cPresente").textContent = conteo.presente;
        document.getElementById("cAusente").textContent = conteo.ausente;
        document.getElementById("cJustificada").textContent = conteo.justificada;
        document.getElementById("cSin").textContent = conteo.sin;
        return conteo;
    }

    formAsistencia.addEventListener("change", contar);

    document.getElementById("todosPresentes").addEventListener("click", function () {
        filas.forEach(function (grupo) {
            grupo.querySelector("input[value=presente]").checked = true;
        });
        contar();
    });

    formAsistencia.addEventListener("submit", function (evento) {
        const conteo = contar();
        if (conteo.sin > 0) {
            evento.preventDefault();
            alert("Te falta marcar " + conteo.sin + " estudiante(s).");
        }
    });

    contar();
}
