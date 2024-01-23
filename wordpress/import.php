<?php
// Habilitar el registro de errores y mostrarlos en pantalla
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Habilitar el registro de errores en un archivo de registro
ini_set('log_errors', 1);
ini_set('error_log', __DIR__ . '/error_log.txt');

// Cargar el archivo wp-load.php para acceder a las funciones de WordPress
require_once(dirname(__FILE__) . '/../wp-load.php');
require_once(dirname(__FILE__) . '/../wp-config.php');
require_once(dirname(__FILE__) . '/../wp-admin/includes/admin.php');

// Función para descargar la imagen desde la URL usando media_sideload_image
function download_image($image_url, $post_id, $hotel_name) {
    $attachment_id = media_sideload_image($image_url, $post_id, $hotel_name, 'id');

    if (!is_wp_error($attachment_id)) {
        return $attachment_id;
    } else {
        error_log('Error al descargar la imagen: ' . $attachment_id->get_error_message());
        return false;
    }
}

// Ruta al archivo CSV
$csv_file = __DIR__ . '/hotel_list.csv';

// Leer datos desde el archivo CSV
if (($handle = fopen($csv_file, 'r')) !== FALSE) {
    // Ignorar la primera fila (encabezados)
    fgetcsv($handle);

    while (($data = fgetcsv($handle, 1000, ',')) !== FALSE) {
        // Obtener datos del CSV
        $hotel_name = $data[0];
        $price = $data[1];
        $score = $data[2];
        $avg_review = $data[3];
        $reviews_count = $data[4];
        $image_url = $data[5];
        $hotel_url = $data[6];
        $popular_facilities = $data[7];
        $city = $data[8];
        $country = $data[9];
        $description = $data[10];
        $online_count = rand(2, 15);

        // Crear un array con los datos del post
        $post_data = array(
            'post_title' => $hotel_name,
            'post_content' => '', // Inicializar el contenido del post
            'post_status' => 'publish',
            'post_type' => 'post',
            'post_author' => 1, // ID del usuario que creó la entrada
        );

        // Insertar el post en WordPress
        $post_id = wp_insert_post($post_data);

        // Verificar si la inserción fue exitosa antes de continuar
        if ($post_id) {

            // Crear el contenido del post en WordPress
            $post_content = "
                <div class='hotel-info'>
                    <p><strong>Desde:</strong> {$price} /noche</p>
                    <p><strong>Puntuación:</strong><a href='{$hotel_url}' target='_blank' style='text-decoration: none;'>{$score} / {$avg_review}</a></p>
                    <p class='align-right'><a href='{$hotel_url}&#map_opened-hotel_sidebar_static_map' class='small-availability-button' target='_blank' style='text-decoration: none;'>Ver ubicación en el mapa</a></p>
                </div>
                <p><a href='{$hotel_url}' target='_blank' style='text-decoration: none;'><img src='{$image_url}' alt='{$hotel_name}'></a></p>
                <p><a href='{$hotel_url}&activeTab=photosGallery' class='small-availability-button' target='_blank' style='text-decoration: none;'>Ver más fotos de {$hotel_name}</a></p>
                
                <p><a href='{$hotel_url}#tab-reviews' target='_blank' style='text-decoration: none;'><strong>{$hotel_name} recibió :</strong> {$reviews_count} calificaciones</a></p>
                
                <p>{$description}</p>
                
                <p>Tú y {$online_count} personas más están viendo este alojamiento, ¡Reserva antes que se agote!</p>
                <p><a href='{$hotel_url}' class='availability-button' target='_blank' style='text-decoration: none;'>Ver Disponibilidad de {$hotel_name}</a></p>
            ";

            // Actualizar el contenido del post con la información adicional
            wp_update_post(array('ID' => $post_id, 'post_content' => $post_content));

            try {
                // Subir y asignar la imagen destacada usando media_sideload_image
                $image_id = download_image($image_url, $post_id, $hotel_name);

                if ($image_id !== false) {
                    // Establecer la imagen destacada
                    set_post_thumbnail($post_id, $image_id);
                }
            } catch (Exception $e) {
                error_log('Error: ' . $e->getMessage() . ' (Código: ' . $e->getCode() . ')');
                continue; // Salir del script de PHP
            }

            // Agregar las categorías
            if (!empty($city) && !empty($country)) {
                // Elimina espacios en blanco alrededor de $city y $country
                $city = trim($city);
                $country = trim($country);

                // Verifica si la categoría del país ya existe
                $country_id = get_cat_ID($country);

                // Si no existe, la crea
                if ($country_id == 0) {
                    $country_args = array(
                        'cat_name' => $country,
                        'category_description' => '', // Puedes ajustar esto si es necesario
                        'category_nicename' => sanitize_title($country),
                        'category_parent' => ''
                    );

                    // Crea la categoría del país y obtiene su ID
                    $country_id = wp_insert_category($country_args);
                }

                // Verifica si la subcategoría de la ciudad ya existe bajo el país
                $city_term = get_term_by('name', $city, 'category');

                // Si no existe, la crea como subcategoría del país
                if (!$city_term) {
                    $city_args = array(
                        'cat_name' => $city,
                        'category_description' => '', // Puedes ajustar esto si es necesario
                        'category_nicename' => sanitize_title($city),
                        'category_parent' => $country_id
                    );

                    // Crea la subcategoría de la ciudad y obtiene su ID
                    $city_id = wp_insert_category($city_args);
                } else {
                    // Si la subcategoría ya existe, obtiene su ID
                    $city_id = $city_term->term_id;
                }

                    // Agrega $city como categoría principal
                    $filtered_categories[] = $city_id;

                    // Asigna la categoría de la ciudad como categoría principal al post
                    wp_set_post_categories($post_id, $filtered_categories, true);

                    // Agrega $country como categoría secundaria
                    wp_set_post_categories($post_id, array($country_id), true);

            }

            // Agregar las etiquetas
            if (!empty($popular_facilities)) {
                $tag_array = explode(',', $popular_facilities);
                wp_set_post_tags($post_id, $tag_array, true);
            }

            echo "Post creado con éxito. ID: {$post_id}\n";
        } else {
            echo "Error al crear el post.\n";
        }
    }

    fclose($handle);
} else {
    echo "Error al abrir el archivo CSV.\n";
}

?>