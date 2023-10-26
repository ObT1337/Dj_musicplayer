import copy

from audio_track import AudioTrack, TrackCollection
from logger import Logger
from PyQt6 import QtGui
from PyQt6.QtCore import (QByteArray, QDataStream, QIODevice, QIODeviceBase,
                          QMimeData, QModelIndex, Qt)
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout,
                             QHBoxLayout, QLabel, QLayout, QLayoutItem,
                             QLineEdit, QMenu, QPushButton, QTableWidget,
                             QTableWidgetItem, QTabWidget, QVBoxLayout,
                             QWidget)
from settings import LoggerSettings

log = Logger("Widgets", LoggerSettings.log_level)


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create tabs
        self.tabs = {}
        # self.tab1 = QWidget()
        # self.tab2 = QWidget()

        # # Add tabs to widget
        # self.addTab(self.tab1, "Tab 1")
        # self.addTab(self.tab2, "Tab 2")

        # # Create layout for tab 1
        # tab1_layout = QVBoxLayout()
        # tab1_layout.addWidget(QLabel("Name:"))
        # tab1_layout.addWidget(QLineEdit())
        # tab1_layout.addWidget(QLabel("Age:"))
        # tab1_layout.addWidget(QLineEdit())
        # tab1_layout.addWidget(QPushButton("Save"))

        # # Create layout for tab 2
        # tab2_layout = QHBoxLayout()
        # tab2_layout.addWidget(QLabel("Address:"))
        # tab2_layout.addWidget(QLineEdit())
        # tab2_layout.addWidget(QPushButton("Search"))

        # # Set layouts for tabs
        # self.tab1.setLayout(tab1_layout)
        # self.tab2.setLayout(tab2_layout)

    def add_tab(self, title, layout):
        tab = QWidget()
        self.tabs[title] = tab
        self.addTab(tab, title)
        tab.setLayout(layout)


class RemovableButton(QWidget):
    def __init__(self, text, layout):
        super().__init__()
        self.text = text
        self.layout = layout
        self.init_ui()

    def init_ui(self):
        button_layout = QHBoxLayout()
        self.setLayout(button_layout)

        self.button = QPushButton(self.text)
        self.button.setFixedHeight(30)
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.button)

        self.remove_button = QPushButton("X")
        self.remove_button.setObjectName("RemoveButton")
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.setFixedSize(20, 30)
        self.remove_button.setStyleSheet("QPushButton#RemoveButton { color: red; }")
        button_layout.addWidget(self.remove_button)

        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.layout.add_widget(self)

    def clicked(self, fnc):
        self.button.clicked.connect(fnc)

    def on_remove(self, fnc):
        self.remove_button.clicked.connect(fnc)


class LimitedGridLayout(QGridLayout):
    def __init__(self, parent=None, max_columns=5):
        super().__init__(parent)
        self.max_columns = max_columns

    def add_widget(self, widget):
        # Calculate the current row and column based on the existing widgets in the layout
        row, col = divmod(self.count(), self.max_columns)

        # If the current row has reached the maximum number of columns, add a new row
        if col == 0:
            self.setRowMinimumHeight(row, widget.sizeHint().height())

        # Add the widget to the layout at the calculated row and column
        self.addWidget(widget, row, col)

    def clear_layout(self):
        to_remove = []
        for i in range(self.count()):
            item = self.itemAt(i)
            if item is None:
                continue
            to_remove.append(item)
        for item in to_remove:
            self.removeItem(item)
            item.widget().deleteLater()


class TrackTable(QTableWidget):
    def __init__(
        self,
        rows=0,
        columns=6,
        parent=None,
        horizontal_header_labels=["#", "Artists", "Track", "BPM", "Genre", "Date"],
        execute_on_cell_click=None,
        parent_window=None,
    ):
        super().__init__(rows, columns, parent)
        self.parent_window = parent_window
        self.setHorizontalHeaderLabels(horizontal_header_labels)
        self.cellDoubleClicked.connect(self.on_cell_clicked)
        self.cellActivated.connect(self.on_cell_clicked)
        self.cellChanged.connect(self.on_cell_changed)
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.verticalHeader().setVisible(False)

        self.sort_order = Qt.SortOrder.AscendingOrder
        self.sort_column = 0
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDropIndicatorShown(True)
        self.all_tracks = TrackCollection()

    def set_row_item(self, item, row: int = None):
        for i, x in enumerate(
            [item.index_item, item.artist, item.title, item.bpm, item.genre]
        ):
            self.setItem(item.index, i, x)

    def add_track(self, track):
        self.all_tracks.add_track(track)
        self.update_table([track])

    def update_table(self, tracks, row=None):
        if row is None:
            row = self.rowCount()
        for track in tracks:
            self.insertRow(row)
            item = TrackTableRow(track, self, row)
            self.set_row_item(item, row)
            row += 1
        self.resize_to_fit_content()

    def resize_to_fit_content(self):
        # Resize the columns to fit the content
        for column in range(self.columnCount()):
            self.resizeColumnToContents(column)

    def on_cell_clicked(self, row, column):
        # Select the whole row
        self.selectRow(row)
        item = self.item(row, 0)
        log.debug(item.parent)
        if row is None:
            return
        index = self.item(row, 0).text()
        log.debug(index)
        assert index.isnumeric()
        index = int(index) - 1
        self.selected_track = self.all_tracks[index]
        self.parent_window.load_track(self.selected_track.path)

    def dropEvent(self, event):
        # Get the source and destination rows
        for row in self.dragging_rows:
            source_row = row

            destination_row = self.indexAt(event.position().toPoint()).row()
            log.debug(f"Destination row:{destination_row}")
            log.debug(f"Source row:{source_row}")
            # If the source and destination rows are the same, do nothing
            if source_row == destination_row:
                return

            # Move the row to the new position
            if destination_row == -1:
                log.debug(f"Destination row == -1")
                destination_row = self.rowCount()
            elif destination_row < source_row:
                log.debug(f"Destination row < source row")
                tmp_row = destination_row + 1
                source_row += 1
                self.insertRow(tmp_row)
                for column in range(self.columnCount()):
                    self.setItem(
                        tmp_row, column, self.takeItem(destination_row, column)
                    )
                for column in range(self.columnCount()):
                    self.setItem(
                        destination_row, column, self.takeItem(source_row, column)
                    )
                self.removeRow(source_row)
                return
            else:
                log.debug(f"Destination row > source Row")
                destination_row += 1

            self.insertRow(destination_row)
            for column in range(self.columnCount()):
                self.setItem(destination_row, column, self.takeItem(source_row, column))
            self.removeRow(source_row)

    def dragEnterEvent(self, event):
        # Accept the event if it has a MIME type of "application/x-qabstractitemmodeldatalist"
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        # Accept the event if it has a MIME type of "application/x-qabstractitemmodeldatalist"
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def startDrag(self, supported_actions):
        # Get the selected row
        selected_rows = self.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            return

        # Create a MIME data object with the selected rows
        mime_data = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODeviceBase.OpenModeFlag.WriteOnly)
        for row in selected_rows:
            stream.writeInt(row.row())
        mime_data.setData("application/x-qabstractitemmodeldatalist", data)

        # Create a drag object and start the drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)

        drag.exec(supported_actions)

    def show_context_menu(self, pos):
        # Create the context menu
        menu = QMenu(self)
        info = menu.addAction("Information")
        # info.triggered.connect(self.parent_window.show_track_info)
        delete = menu.addAction("Delete Track from Playlist")
        delete_submenu = QMenu(menu)
        delete_submenu.addAction("Yes")
        delete_submenu.addAction("No")
        delete.setMenu(delete_submenu)

        add_to_pl = menu.addAction("Add Track to Playlist")
        add_submenu = QMenu(menu)
        to_new = add_submenu.addAction("New Playlist")
        # to_new.triggered.connect(self.parent_window.add_to_new_pl)

        for index, playlist in enumerate(self.parent_window.collection.playlists):
            plm = add_submenu.addAction(playlist.name)
            # plm.triggered.connect(lambda checked, index=index: self.parent_window.add_to_pl(index))
            plm.triggered.connect(lambda checked, index=index: print(index))

        add_to_pl.setMenu(add_submenu)

        # add_to_pl.triggered.connect(self.parent_window.add_to_pl)

        # Show the context menu at the position of the right-click
        menu.exec(self.mapToGlobal(pos))

    def on_header_clicked(self, column):
        # Sort the table by the clicked column
        if self.sort_column == column:
            self.sort_order = (
                Qt.SortOrder.DescendingOrder
                if self.sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self.sort_column = column
            self.sort_order = Qt.SortOrder.AscendingOrder
        self.sortItems(column, self.sort_order)

    def on_cell_changed(self, row, column):
        self.resizeColumnToContents(column)

    def mousePressEvent(self, event):
        # Save the rows being dragged
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_rows = [
                index.row() for index in self.selectionModel().selectedRows()
            ]
        super().mousePressEvent(event)

    # def mouseReleaseEvent(self, event) -> None:
    #     if event.button() == Qt.MouseButton.LeftButton:
    #         self.selected_tracks = self.selectedItems()
    #         for track in self.selected_tracks:
    #             log.debug(track)
    #     super().mouseReleaseEvent(event)

    def clearContents(self):
        self.setRowCount(0)  # Remove all rows from the table
        self.all_tracks = []  # Set the all_tracks attribute to an empty list
        super().clearContents()


class TrackTableRow(QTableWidgetItem):
    def __init__(self, track: AudioTrack, table: TrackTable, index=0) -> None:
        super().__init__()
        self.track = track
        self.table = table
        self.index = index
        self.index_item = NumericTableWidgetItem(str(index + 1))
        self.artist = QTableWidgetItem(track.artist)
        self.title = QTableWidgetItem(track.title)
        self.bpm = NumericTableWidgetItem(track.bpm)
        self.genre = QTableWidgetItem(track.genre)

        for item in [self.index_item, self.artist, self.title, self.bpm, self.genre]:
            item.parent = self


    class NumericTableWidgetItem(QTableWidgetItem):
        def __init__(self, text):
            super().__init__(text)

        def __lt__(self, other):
            try:
                return float(self.text()) < float(other.text())
            except ValueError:
                return super().__lt__(other)

        def setData(self, role, value):
            #FIXME: EditRole unknown
            if role == Qt.EditRole:
                try:
                    float(value)
                    super().setData(role, value)
                except ValueError:
                    pass
            else:
                super().setData(role, value)
