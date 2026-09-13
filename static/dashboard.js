let grafico = null;

document.addEventListener("DOMContentLoaded", () => {
    // Inicializar vistas dinámicas
    cargarCategorias();
    cargarDashboard();
    cargarTopEmpleados();
    cargarRolesYEmpleados();

    // Control de navegación por pestañas (Sidebar)
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    // Manejo del formulario para agregar nuevas categorías (POST)
const formCat = document.getElementById("formNuevaCategoria");
if (formCat) {
    formCat.addEventListener("submit", async (e) => {
        e.preventDefault();
        const inputNombre = document.getElementById("nombreCategoria");
        const nombre = inputNombre.value.trim();

        if (!nombre) return;

        try {
            const res = await fetch("/api/v1/categorias", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nombre: nombre })
            });

            if (res.ok) {
                inputNombre.value = "";
                await cargarCategorias(); // Recarga la lista de la pestaña y el desplegable del filtro
            } else {
                const errorData = await res.json();
                alert(errorData.detail || "Error al crear la categoría");
            }
        } catch (e) {
            console.error("Error en la petición POST de categoría:", e);
        }
    });
}

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            navButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            const targetTab = document.getElementById(tabId);
            if (targetTab) targetTab.classList.add("active");
        });
    });

    // Eventos de Filtros en el Dashboard
    const btnFiltrar = document.getElementById("btnFiltrar");
    const btnLimpiar = document.getElementById("btnLimpiar");

    if (btnFiltrar) btnFiltrar.addEventListener("click", cargarDashboard);
    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", () => {
            document.getElementById("categoria").value = "";
            document.getElementById("fecha_inicio").value = "";
            document.getElementById("fecha_fin").value = "";
            cargarDashboard();
        });
    }
});

// 1. Cargar Categorías en el Filtro y en la pestaña CRUD
async function cargarCategorias() {
    try {
        const res = await fetch("/api/v1/categorias");
        const categorias = await res.json();
        
        const select = document.getElementById("categoria");
        const listaCrud = document.getElementById("listaCategoriasCrud");

        if (select) {
            select.innerHTML = '<option value="">Todas las categorías</option>';
            categorias.forEach(cat => {
                const option = document.createElement("option");
                option.value = cat;
                option.textContent = cat;
                select.appendChild(option);
            });
        }

        if (listaCrud) {
            listaCrud.innerHTML = "";
            categorias.forEach(cat => {
                listaCrud.innerHTML += `
                    <li style="padding: 12px 16px; background: #fff; border: 1px solid var(--border); border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <span>🏷️ <strong>${cat}</strong></span>
                        <span style="color: #16a34a; font-size: 12px; font-weight: 600;">Activa</span>
                    </li>
                `;
            });
        }
    } catch (e) {
        console.error("Error al cargar categorías:", e);
    }
}

// 2. Cargar KPIs, Tabla y Gráfico del Dashboard
async function cargarDashboard() {
    const elCat = document.getElementById("categoria");
    const elInicio = document.getElementById("fecha_inicio");
    const elFin = document.getElementById("fecha_fin");

    const cat = elCat ? elCat.value : "";
    const inicio = elInicio ? elInicio.value : "";
    const fin = elFin ? elFin.value : "";

    let query = new URLSearchParams();
    if (cat) query.append("categoria", cat);
    if (inicio) query.append("fecha_inicio", inicio);
    if (fin) query.append("fecha_fin", fin);

    // Cargar KPIs
    try {
        const resKpi = await fetch(`/api/v1/resumen?${query}`);
        const kpis = await resKpi.json();
        
        document.getElementById("totalIngresos").textContent = `$${kpis.total_ingresos.toFixed(2)}`;
        document.getElementById("totalVentas").textContent = kpis.total_ventas;
        document.getElementById("ticketPromedio").textContent = `$${kpis.ticket_promedio.toFixed(2)}`;
    } catch (e) {
        console.error("Error al cargar KPIs:", e);
    }

    // Cargar Ventas y Gráfico
    try {
        const resVentas = await fetch(`/api/v1/ventas?${query}`);
        const ventas = await resVentas.json();
        
        const tbody = document.getElementById("tablaVentas");
        if (tbody) tbody.innerHTML = "";
        
        const resumenCategorias = {};

        ventas.forEach(v => {
            if (tbody) {
                tbody.innerHTML += `
                    <tr>
                        <td>${v.fecha}</td>
                        <td>${v.categoria}</td>
                        <td>$${v.monto.toFixed(2)}</td>
                    </tr>
                `;
            }
            resumenCategorias[v.categoria] = (resumenCategorias[v.categoria] || 0) + v.monto;
        });

        actualizarGrafico(resumenCategorias);
    } catch (e) {
        console.error("Error al cargar ventas:", e);
    }
}

function actualizarGrafico(datos) {
    const canvas = document.getElementById("graficoVentas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (grafico) grafico.destroy();

    grafico = new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(datos),
            datasets: [{
                label: "Ventas ($)",
                data: Object.values(datos),
                backgroundColor: "#2563eb",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } }
        }
    });
}

// 3. Cargar Pestaña Empleados del Mes (Ranking)
async function cargarTopEmpleados() {
    try {
        const res = await fetch("/api/v1/empleados/top");
        const top = await res.json();
        
        const tbody = document.querySelector("#tab-empleados tbody");
        if (!tbody) return;

        tbody.innerHTML = "";
        const medallas = ["🥇 1°", "🥈 2°", "🥉 3°"];

        top.forEach((emp, index) => {
            const pos = medallas[index] || `${index + 1}°`;
            tbody.innerHTML += `
                <tr>
                    <td><strong>${pos}</strong></td>
                    <td>${emp.empleado}</td>
                    <td>${emp.total_ventas} ventas</td>
                    <td>$${emp.monto_recaudado.toFixed(2)}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error al cargar ranking de empleados:", e);
    }
}

// 4. Cargar Pestaña Roles y Permisos
async function cargarRolesYEmpleados() {
    try {
        const res = await fetch("/api/v1/empleados");
        const empleados = await res.json();
        
        const tbody = document.querySelector("#tab-roles tbody");
        if (!tbody) return;

        tbody.innerHTML = "";
        empleados.forEach(emp => {
            const nombreRol = emp.rol ? emp.rol.nombre : "Sin Rol";
            const badgeColor = nombreRol === "Super Admin" ? "background: #dbeafe; color: #1e40af" : 
                             nombreRol === "Gerente" ? "background: #fef3c7; color: #92400e" : "background: #e2e8f0; color: #334155";

            tbody.innerHTML += `
                <tr>
                    <td><strong>${emp.nombre}</strong><br><small style="color: var(--text-muted);">${emp.email}</small></td>
                    <td><span style="${badgeColor}; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">${nombreRol}</span></td>
                    <td><span style="color: #16a34a; font-weight: 600;">● Activo</span></td>
                    <td><button class="btn-secondary" style="padding: 4px 10px; font-size: 12px;">Editar</button></td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error al cargar roles y empleados:", e);
    }
}