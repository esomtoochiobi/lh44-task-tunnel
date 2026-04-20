"""
Task Tunnel - Frontend (gui.py)
Team LH44 | CSCE 432/632

This file owns the entire UI layer. It imports stubs from `backend.py`
(to be implemented by the backend/database teammates). Swap the stubs
out for real implementations without touching this file.
"""

import wx

from database import init_db
from backend import get_profiles, save_profile, delete_profile, launch_profile

# ---------------------------------------------------------------------------
# add / edit profile dialog
# ---------------------------------------------------------------------------
class ProfileDialog(wx.Dialog):
    """
    Modal dialog for creating a new Task Profile.
    Collect: profile name + one resource per line (URL, file path, or app).
    """

    def __init__(self, parent, title="New Task Profile"):
        super().__init__(parent, title=title, size=(480, 380),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # --- profile name ---
        vbox.Add(wx.StaticText(panel, label="Profile Name:"), flag=wx.LEFT | wx.TOP, border=16)
        self.name_ctrl = wx.TextCtrl(panel)
        self.name_ctrl.SetHint("e.g. Database Assignment")
        vbox.Add(self.name_ctrl, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=16)

        # --- resources ---
        vbox.Add(wx.StaticText(panel, label="Resources (one per line — URL, file path, or app):"),
                 flag=wx.LEFT | wx.TOP, border=16)
        self.resources_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.resources_ctrl.SetHint("https://canvas.tamu.edu\n/Users/you/notes.txt\nSlack")
        vbox.Add(self.resources_ctrl, proportion=1,
                 flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=16)

        # --- buttons ---
        btn_sizer = wx.StdDialogButtonSizer()
        self.save_btn = wx.Button(panel, wx.ID_OK, label="Save Profile")
        self.save_btn.SetDefault()
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, label="Cancel")
        btn_sizer.AddButton(self.save_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        vbox.Add(btn_sizer, flag=wx.EXPAND | wx.ALL, border=16)

        panel.SetSizer(vbox)
        self.save_btn.Bind(wx.EVT_BUTTON, self._on_save)

    def _on_save(self, event):
        if not self.name_ctrl.GetValue().strip():
            wx.MessageBox("Please enter a profile name.", "Missing Name",
                          wx.OK | wx.ICON_WARNING, self)
            return
        if not self.get_resources():
            wx.MessageBox("Please add at least one resource.", "Missing Resources",
                          wx.OK | wx.ICON_WARNING, self)
            return
        event.Skip()  # let wx close the dialog with ID_OK

    def get_name(self) -> str:
        return self.name_ctrl.GetValue().strip()

    def get_resources(self) -> list[str]:
        lines = self.resources_ctrl.GetValue().splitlines()
        return [line.strip() for line in lines if line.strip()]


# ---------------------------------------------------------------------------
# main application window
# ---------------------------------------------------------------------------
class MainFrame(wx.Frame):
    """
    Primary window. Left panel: profile list. Right panel: profile detail + actions.
    """

    def __init__(self):
        super().__init__(None, title="Task Tunnel", size=(700, 480),
                         style=wx.DEFAULT_FRAME_STYLE)

        self.profiles = []   # cached from backend
        self._build_ui()
        self._refresh_profiles()
        self.Centre()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.HORIZONTAL)

        # ---- left: profile list ----
        left = wx.BoxSizer(wx.VERTICAL)

        header = wx.StaticText(panel, label="Task Profiles")
        header.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left.Add(header, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=12)

        self.profile_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.profile_list.SetToolTip("Select a profile to view or launch it")
        left.Add(self.profile_list, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=12)

        add_btn = wx.Button(panel, label="＋  New Profile")
        add_btn.SetToolTip("Create a new Task Profile")
        left.Add(add_btn, flag=wx.EXPAND | wx.ALL, border=12)

        root.Add(left, proportion=1, flag=wx.EXPAND)

        # ---- divider ----
        root.Add(wx.StaticLine(panel, style=wx.LI_VERTICAL), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=8)

        # ---- right: detail + actions ----
        right = wx.BoxSizer(wx.VERTICAL)

        self.detail_label = wx.StaticText(panel, label="Select a profile to get started.")
        self.detail_label.Wrap(280)
        right.Add(self.detail_label, flag=wx.ALL, border=16)

        self.resources_box = wx.StaticBoxSizer(wx.VERTICAL, panel, label="Resources")
        self.resources_text = wx.StaticText(panel, label="")
        self.resources_box.Add(self.resources_text, flag=wx.ALL, border=8)
        right.Add(self.resources_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=16)

        right.AddStretchSpacer()

        self.launch_btn = wx.Button(panel, label="🚀  Launch Profile")
        self.launch_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.launch_btn.SetToolTip("Open all resources for this profile at once")
        self.launch_btn.Disable()
        right.Add(self.launch_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=16)

        self.delete_btn = wx.Button(panel, label="🗑  Delete Profile")
        self.delete_btn.SetToolTip("Remove this profile")
        self.delete_btn.Disable()
        right.Add(self.delete_btn, flag=wx.EXPAND | wx.ALL, border=16)

        root.Add(right, proportion=1, flag=wx.EXPAND)

        panel.SetSizer(root)

        # ---- event bindings ----
        self.profile_list.Bind(wx.EVT_LISTBOX, self._on_select)
        add_btn.Bind(wx.EVT_BUTTON, self._on_add)
        self.launch_btn.Bind(wx.EVT_BUTTON, self._on_launch)
        self.delete_btn.Bind(wx.EVT_BUTTON, self._on_delete)

    # ------------------------------------------------------------------
    # data / state
    # ------------------------------------------------------------------
    def _refresh_profiles(self):
        self.profiles = get_profiles()
        self.profile_list.Clear()
        for p in self.profiles:
            self.profile_list.Append(p["name"])
        self._clear_detail()

    def _clear_detail(self):
        self.detail_label.SetLabel("Select a profile to get started.")
        self.resources_text.SetLabel("")
        self.launch_btn.Disable()
        self.delete_btn.Disable()

    def _selected_profile(self):
        idx = self.profile_list.GetSelection()
        if idx == wx.NOT_FOUND:
            return None
        return self.profiles[idx]

    # ------------------------------------------------------------------
    # event handlers
    # ------------------------------------------------------------------
    def _on_select(self, event):
        profile = self._selected_profile()
        if not profile:
            return
        self.detail_label.SetLabel(f"Profile: {profile['name']}")
        resources = profile.get("resources", [])
        self.resources_text.SetLabel("\n".join(resources) if resources else "(no resources)")
        self.launch_btn.Enable()
        self.delete_btn.Enable()

    def _on_add(self, event):
        dlg = ProfileDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.get_name()
            resources = dlg.get_resources()
            if save_profile(name, resources):
                self._refresh_profiles()
            else:
                wx.MessageBox("Failed to save profile. Check backend.", "Error",
                              wx.OK | wx.ICON_ERROR, self)
        dlg.Destroy()

    def _on_launch(self, event):
        profile = self._selected_profile()
        if not profile:
            return
        success = launch_profile(profile["id"])
        if not success:
            wx.MessageBox("Some resources failed to open. Check backend.", "Launch Error",
                          wx.OK | wx.ICON_WARNING, self)

    def _on_delete(self, event):
        profile = self._selected_profile()
        if not profile:
            return
        confirm = wx.MessageBox(
            f"Delete profile \"{profile['name']}\"?", "Confirm Delete",
            wx.YES_NO | wx.ICON_QUESTION, self
        )
        if confirm == wx.YES:
            if delete_profile(profile["id"]):
                self._refresh_profiles()
            else:
                wx.MessageBox("Failed to delete profile.", "Error", wx.OK | wx.ICON_ERROR, self)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db(include_dummy=True)
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
