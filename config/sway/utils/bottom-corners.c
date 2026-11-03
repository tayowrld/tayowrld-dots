#include <gtk/gtk.h>
#include <gtk-layer-shell.h>
#include <cairo.h>

#define RADIUS 18

static gboolean draw_corner(GtkWidget *widget, cairo_t *cr, gpointer data) {
    int corner = GPOINTER_TO_INT(data);
    gboolean right = corner & 1;
    gboolean top = corner & 2;
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
    cairo_set_source_rgba(cr, 0, 0, 0, 0);
    cairo_paint(cr);
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER);
    cairo_set_source_rgb(cr, 0, 0, 0);
    cairo_rectangle(cr, 0, 0, RADIUS, RADIUS);
    cairo_arc(cr, right ? 0 : RADIUS, top ? RADIUS : 0, RADIUS, 0, 2 * G_PI);
    cairo_set_fill_rule(cr, CAIRO_FILL_RULE_EVEN_ODD);
    cairo_fill(cr);
    return TRUE;
}

static void make_corner(GdkMonitor *monitor, gboolean right, gboolean top) {
    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    GdkScreen *screen = gtk_widget_get_screen(window);
    GdkVisual *visual = gdk_screen_get_rgba_visual(screen);
    if (visual) gtk_widget_set_visual(window, visual);
    gtk_widget_set_app_paintable(window, TRUE);
    gtk_window_set_default_size(GTK_WINDOW(window), RADIUS, RADIUS);
    gtk_widget_set_size_request(window, RADIUS, RADIUS);
    gtk_layer_init_for_window(GTK_WINDOW(window));
    gtk_layer_set_monitor(GTK_WINDOW(window), monitor);
    gtk_layer_set_namespace(GTK_WINDOW(window), "screen-corners");
    gtk_layer_set_layer(GTK_WINDOW(window), GTK_LAYER_SHELL_LAYER_OVERLAY);
    gtk_layer_set_anchor(GTK_WINDOW(window), top ? GTK_LAYER_SHELL_EDGE_TOP : GTK_LAYER_SHELL_EDGE_BOTTOM, TRUE);
    gtk_layer_set_anchor(GTK_WINDOW(window), right ? GTK_LAYER_SHELL_EDGE_RIGHT : GTK_LAYER_SHELL_EDGE_LEFT, TRUE);
    gtk_layer_set_keyboard_mode(GTK_WINDOW(window), GTK_LAYER_SHELL_KEYBOARD_MODE_NONE);
    gtk_layer_set_exclusive_zone(GTK_WINDOW(window), -1);
    g_signal_connect(window, "draw", G_CALLBACK(draw_corner), GINT_TO_POINTER((top ? 2 : 0) | (right ? 1 : 0)));
    gtk_widget_show_all(window);
    cairo_region_t *empty = cairo_region_create();
    gdk_window_input_shape_combine_region(gtk_widget_get_window(window), empty, 0, 0);
    cairo_region_destroy(empty);
}

int main(int argc, char **argv) {
    gtk_init(&argc, &argv);
    GdkDisplay *display = gdk_display_get_default();
    GdkMonitor *monitor = gdk_display_get_primary_monitor(display);
    if (!monitor) monitor = gdk_display_get_monitor(display, 0);
    if (!monitor) return 1;
    make_corner(monitor, FALSE, FALSE);
    make_corner(monitor, TRUE, FALSE);
    make_corner(monitor, FALSE, TRUE);
    make_corner(monitor, TRUE, TRUE);
    gtk_main();
    return 0;
}
