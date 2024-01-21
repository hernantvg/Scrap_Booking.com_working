<?php
// Cargar el archivo wp-load.php para acceder a las funciones de WordPress
require_once(dirname(__FILE__) . '/../wp-load.php');

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
        $image_links = explode(',', $data[5]);
        $hotel_url = $data[6];
        $popular_facilities = json_decode($data[7], true);
        $city = $data[8];
        $country = $data[9];
        $description = $data[10];
        $online_count = rand(2, 15);


        // Crear un array con los datos del post
        $post_data = array(
            'post_title'   => $hotel_name,
            'post_content' => '', // Inicializar el contenido del post
            'post_status'  => 'publish',
            'post_type'    => 'post',
        );

        // Insertar el post en WordPress
        $post_id = wp_insert_post($post_data);

        // Verificar si la inserción fue exitosa antes de continuar
        if ($post_id) {
            // Establecer la primera imagen como imagen destacada
            if (!empty($image_links[0])) {
                $featured_image_url = $image_links[0];
                $attachment_id = upload_image_from_url($featured_image_url, $post_id);

                if ($attachment_id) {
                    // Establecer la imagen descargada como imagen destacada
                    set_post_thumbnail($post_id, $attachment_id);
                }
            }

            // Crear el contenido del post en WordPress
            $post_content = "
                <div class='hotel-info'>
                        <p><strong>Desde:</strong> {$price} /noche</p>
                        <p><strong>Puntuación:</strong> {$score} / {$avg_review}</p>
                        <p class='align-right'><a href='{$hotel_url}&#map_opened-hotel_sidebar_static_map' class='small-availability-button' target='_blank' style='text-decoration: none;'>Ver ubicación en el mapa</a></p>
                </div>
                <p><a href='{$hotel_url}' target='_blank' style='text-decoration: none;'><img src='{$featured_image_url}' alt='Hotel Image'></a></p>
                <p><a href='{$hotel_url}&activeTab=photosGallery' class='small-availability-button' target='_blank' style='text-decoration: none;'>Ver más fotos de {$hotel_name}</a></p>
                
                <p><a href='{$hotel_url}#tab-reviews' target='_blank' style='text-decoration: none;'><strong>{$hotel_name} recibió :</strong> {$reviews_count} calificaciones</a></p>
                
                <p>{$description}</p>
                
                <p>Tú y {$online_count} personas más están viendo este alojamiento, ¡Reserva antes que se agote!</p>
                <p><a href='{$hotel_url}' class='availability-button' target='_blank' style='text-decoration: none;'>Ver Disponibilidad de {$hotel_name}</a></p>
            ";

            // Agregar las popular facilities como tags al contenido del post
            wp_set_post_tags($post_id, $popular_facilities, true);

            // // Categorizar por país (country) y ciudad (city)
            // $country_term = wp_insert_term($country, 'country');
            // $city_term = wp_insert_term($city, 'city', array('parent' => $country_term['term_id']));

            // // Asignar las categorías al post
            // wp_set_post_categories($post_id, array($country_term['term_id'], $city_term['term_id']), true);


            // Actualizar el contenido del post con la información adicional
            wp_update_post(array('ID' => $post_id, 'post_content' => $post_content));

            echo "Post creado con éxito. ID: {$post_id}\n";
        } else {
            echo "Error al crear el post.\n";
        }
    }

    fclose($handle);
} else {
    echo "Error al abrir el archivo CSV.\n";
}

// Función para subir imagen desde URL y devolver el ID del archivo adjunto
function upload_image_from_url($image_url, $post_id) {
    $upload_dir = wp_upload_dir();
    $image_data = file_get_contents($image_url);
    $filename = basename($image_url);
    if (wp_mkdir_p($upload_dir['path'])) {
        $file = $upload_dir['path'] . '/' . $filename;
    } else {
        $file = $upload_dir['basedir'] . '/' . $filename;
    }
    file_put_contents($file, $image_data);

    $wp_filetype = wp_check_filetype($filename, null);
    $attachment = array(
        'post_mime_type' => $wp_filetype['type'],
        'post_title'     => sanitize_file_name($filename),
        'post_content'   => '',
        'post_status'    => 'inherit',
    );

    $attachment_id = wp_insert_attachment($attachment, $file, $post_id);
    if (!is_wp_error($attachment_id)) {
        require_once(ABSPATH . 'wp-admin/includes/image.php');
        $attachment_data = wp_generate_attachment_metadata($attachment_id, $file);
        wp_update_attachment_metadata($attachment_id, $attachment_data);
        return $attachment_id;
    }
    return false;
}
?>
